from django.db import transaction
from django.db.models import Count, Prefetch
from rest_framework.exceptions import ValidationError

from .grade_matching import reconcile_enabled_mappings
from .models import (
    AcademicConfiguration,
    AcademicYear,
    ClassRoom,
    Curriculum,
    CurriculumFramework,
    CurriculumTrack,
    GradeLevel,
    GradeLevelTrackMapping,
    YearLevel,
)


def apply_key_academic_functions(data):
    """Persist validated Key Academic Functions settings atomically."""
    with transaction.atomic():
        configuration = AcademicConfiguration.load()
        for field, value in data['configuration'].items():
            setattr(configuration, field, value)
        configuration.save(update_fields=list(data['configuration']))

        for option_data in data['curricula']:
            option = option_data['id']
            option.is_enabled = option_data['is_enabled']
            update_fields = ['is_enabled']
            if option.is_customizable:
                option.short_name = option_data['short_name']
                option.full_title = option_data['full_title']
                update_fields.extend(['short_name', 'full_title'])
            option.save(update_fields=update_fields)
            if option.is_enabled:
                ensure_option_records(option)


def ensure_option_records(option):
    framework, _ = CurriculumFramework.objects.get_or_create(
        name=option.provider,
        defaults={'order': option.order},
    )
    track, _ = CurriculumTrack.objects.get_or_create(
        framework=framework,
        name=option.name,
        defaults={'order': option.order, 'academic_option': option},
    )
    if track.academic_option_id not in (None, option.id):
        raise ValidationError({'curricula': f'{option.name} is already linked to another academic option.'})
    if track.academic_option_id != option.id:
        track.academic_option = option
        track.save(update_fields=['academic_option'])

    if not option.curriculums.exists():
        curriculum, _ = Curriculum.objects.get_or_create(name=option.name)
        curriculum.academic_options.add(option)

    for year_level in YearLevel.objects.all():
        GradeLevelTrackMapping.objects.get_or_create(
            year_level=year_level,
            track=track,
            defaults={'custom_label': ''},
        )


def enabled_tracks():
    return CurriculumTrack.objects.filter(
        academic_option__is_enabled=True,
    ).select_related('academic_option').order_by('framework__order', 'order')


def enabled_frameworks(tracks):
    return CurriculumFramework.objects.filter(tracks__in=tracks).distinct().prefetch_related(
        Prefetch('tracks', queryset=tracks),
    )


def default_academic_year():
    return AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()


def year_level_stats(academic_year):
    """Class and student counts per year level for one academic year."""
    stats = {}
    if not academic_year:
        return stats
    classroom_counts = (
        ClassRoom.objects.filter(academic_year=academic_year, grade_level__year_level__isnull=False)
        .values('grade_level__year_level_id')
        .annotate(classes=Count('id'))
    )
    student_counts = (
        GradeLevel.objects.filter(
            year_level__isnull=False,
            enrollments__academic_year=academic_year,
            enrollments__is_trial=False,
        )
        .values('year_level_id')
        .annotate(students=Count('enrollments', distinct=True))
    )
    for row in classroom_counts:
        stats.setdefault(row['grade_level__year_level_id'], {})['classes'] = row['classes']
    for row in student_counts:
        stats.setdefault(row['year_level_id'], {})['students'] = row['students']
    return stats


def build_grid_mappings(year_levels, tracks, stats_by_year_level):
    """Cell map keyed '<year_level_id>:<track_id>', filling cells with no stored mapping."""
    mappings = GradeLevelTrackMapping.objects.filter(
        track__academic_option__is_enabled=True,
    ).select_related('year_level', 'track')

    mapping_by_cell = {}
    for mapping in mappings:
        stats = stats_by_year_level.get(mapping.year_level_id, {'classes': 0, 'students': 0})
        mapping_by_cell[f'{mapping.year_level_id}:{mapping.track_id}'] = {
            'is_enabled': mapping.is_enabled,
            'custom_label': mapping.custom_label,
            'stats': {'classes': stats.get('classes', 0), 'students': stats.get('students', 0)},
        }
    for year_level in year_levels:
        for track in tracks:
            mapping_by_cell.setdefault(
                f'{year_level.id}:{track.id}',
                {
                    'is_enabled': False,
                    'custom_label': '',
                    'stats': stats_by_year_level.get(year_level.id, {'classes': 0, 'students': 0}),
                },
            )
    return mapping_by_cell


def save_years_levels_grid(data):
    """Persist the grid payload, then reconcile grade levels. Returns the reconciliation summary."""
    selected_track_ids = set(
        CurriculumTrack.objects.filter(academic_option__is_enabled=True).values_list('id', flat=True)
    )

    with transaction.atomic():
        academic_year = data['academic_year']
        academic_year.grade_numbering_format = data['grade_numbering_format']
        academic_year.save(update_fields=['grade_numbering_format'])

        for cell in data['mappings']:
            if cell['track'] not in selected_track_ids:
                continue
            GradeLevelTrackMapping.objects.update_or_create(
                year_level_id=cell['year_level'],
                track_id=cell['track'],
                defaults={
                    'is_enabled': cell['is_enabled'],
                    'custom_label': cell.get('custom_label', ''),
                },
            )
    return reconcile_enabled_mappings()
