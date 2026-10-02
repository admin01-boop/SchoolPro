from django.test import TestCase

from academics.grade_matching import assignable_grade_level_ids, reconcile_enabled_mappings
from academics.models import (
    AcademicCurriculumOption,
    CurriculumFramework,
    CurriculumTrack,
    GradeLevel,
    GradeLevelTrackMapping,
    YearLevel,
)


class CanonicalEnrollmentLevelTests(TestCase):
    def test_enabled_mapping_reports_year_levels_without_grade_records(self):
        year_level = YearLevel.objects.create(name='EY-1', order=1)
        framework = CurriculumFramework.objects.create(name='Cambridge', order=1)
        option = AcademicCurriculumOption.objects.create(
            code='test-canonical-level', provider='Cambridge', name='Lower Secondary', is_enabled=True,
        )
        track = CurriculumTrack.objects.create(
            framework=framework, name='Lower Secondary', academic_option=option, order=1,
        )
        GradeLevelTrackMapping.objects.create(year_level=year_level, track=track, is_enabled=True, custom_label='K1')

        summary = reconcile_enabled_mappings()
        self.assertEqual(summary['linked'], 0)
        self.assertEqual(summary['unmatched'], [{'label': 'EY-1', 'track': 'Lower Secondary'}])

    def test_assignable_grade_level_ids_only_includes_enabled_linked_mappings(self):
        year_level = YearLevel.objects.create(name='Year 7', order=7)
        framework = CurriculumFramework.objects.create(name='Cambridge', order=1)
        option = AcademicCurriculumOption.objects.create(
            code='test-year-7-level', provider='Cambridge', name='Lower Secondary', is_enabled=True,
        )
        track = CurriculumTrack.objects.create(
            framework=framework, name='Lower Secondary', academic_option=option, order=1,
        )
        grade = GradeLevel.objects.create(name='Year 7 (Grade 6)', order=7, year_level=year_level)
        GradeLevelTrackMapping.objects.create(
            year_level=year_level, track=track, is_enabled=True, custom_label='Custom name',
        )
        self.assertEqual(assignable_grade_level_ids(), {grade.id})

