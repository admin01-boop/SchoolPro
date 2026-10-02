from django.db import migrations


FRAMEWORK_ORDER = {
    'International Baccalaureate': 10,
    'Pearson Edexcel': 20,
    'Cambridge Assessment International Education': 30,
    'International Curriculum Association': 40,
    'The College Board': 50,
    'National Curriculum': 60,
    'International Early Years Curriculum': 70,
}

TRACK_ORDER = {
    'ib-primary-years': 10,
    'ib-middle-years': 20,
    'ib-career-related': 30,
    'ib-diploma': 40,
    'pearson-international-gcses': 10,
    'pearson-btec': 20,
    'pearson-advanced-levels': 30,
    'ica-primary-curriculum': 10,
    'ica-middle-years': 20,
    'cambridge-lower-secondary': 10,
    'cambridge-igcse': 20,
    'cambridge-advanced': 30,
    'cambridge-primary': 40,
    'national-primary-school': 10,
    'national-middle-school': 20,
    'national-high-school': 30,
}

CURRICULUM_ALIASES = {
    'cambridge-advanced': ['Cambridge AS'],
}


def materialize_academic_curriculum_catalogue(apps, schema_editor):
    AcademicCurriculumOption = apps.get_model('academics', 'AcademicCurriculumOption')
    Curriculum = apps.get_model('academics', 'Curriculum')
    CurriculumFramework = apps.get_model('academics', 'CurriculumFramework')
    CurriculumTrack = apps.get_model('academics', 'CurriculumTrack')
    GradeLevelTrackMapping = apps.get_model('academics', 'GradeLevelTrackMapping')
    YearLevel = apps.get_model('academics', 'YearLevel')
    alias = schema_editor.connection.alias

    for option in AcademicCurriculumOption.objects.using(alias).all():
        framework, _ = CurriculumFramework.objects.using(alias).get_or_create(
            name=option.provider,
            defaults={'order': FRAMEWORK_ORDER.get(option.provider, option.order)},
        )
        order = TRACK_ORDER.get(option.code, option.order)
        track, _ = CurriculumTrack.objects.using(alias).get_or_create(
            framework_id=framework.id,
            name=option.name,
            defaults={'order': order, 'academic_option_id': option.id},
        )
        if track.academic_option_id not in (None, option.id):
            continue
        update_fields = []
        if track.academic_option_id != option.id:
            track.academic_option_id = option.id
            update_fields.append('academic_option')
        if track.order != order:
            track.order = order
            update_fields.append('order')
        if update_fields:
            track.save(update_fields=update_fields)

        for level_id in YearLevel.objects.using(alias).values_list('id', flat=True):
            GradeLevelTrackMapping.objects.using(alias).get_or_create(
                year_level_id=level_id,
                track_id=track.id,
                defaults={'is_enabled': False, 'custom_label': ''},
            )

        for curriculum_name in CURRICULUM_ALIASES.get(option.code, [option.name]):
            curriculum, _ = Curriculum.objects.using(alias).get_or_create(name=curriculum_name)
            curriculum.academic_options.add(option)


def reverse_materialized_catalogue(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0010_order_curriculum_frameworks'),
    ]

    operations = [
        migrations.RunPython(materialize_academic_curriculum_catalogue, reverse_materialized_catalogue),
    ]
