"""Queries enrollment grades enabled through selected curricula and Years & Levels rows."""
from .models import GradeLevel, GradeLevelTrackMapping


def assignable_grade_level_ids():
    """Ids of GradeLevels currently enabled for assignment via the Years & Levels grid."""
    enabled_year_levels = GradeLevelTrackMapping.objects.filter(
        is_enabled=True,
        track__academic_option__is_enabled=True,
    ).values_list('year_level_id', flat=True)
    return set(GradeLevel.objects.filter(year_level_id__in=enabled_year_levels).values_list('id', flat=True))


def reconcile_enabled_mappings():
    """Report enabled cells that have no enrollment grades linked to their standard row."""
    mappings = GradeLevelTrackMapping.objects.filter(
        is_enabled=True,
        track__academic_option__is_enabled=True,
    ).select_related('year_level', 'track')
    linked = 0
    unmatched = []
    for mapping in mappings:
        if mapping.year_level.grade_levels.exists():
            linked += 1
        else:
            unmatched.append({'label': mapping.year_level.name, 'track': mapping.track.name})
    return {'linked': linked, 'ambiguous': [], 'unmatched': unmatched}
