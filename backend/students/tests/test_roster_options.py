from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import (
    AcademicCurriculumOption,
    AcademicYear,
    CurriculumFramework,
    CurriculumTrack,
    GradeLevel,
    GradeLevelTrackMapping,
    YearLevel,
)
from accounts.models import User
from students.models import Guardian


class RosterFilterOptionsTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

        self.year_level = YearLevel.objects.create(name='Year 7', order=7)
        self.framework = CurriculumFramework.objects.create(name='Cambridge', order=1)
        self.option = AcademicCurriculumOption.objects.create(
            code='test-cambridge-lower-secondary', provider='Cambridge',
            name='Cambridge Lower Secondary', is_enabled=True,
        )
        self.track = CurriculumTrack.objects.create(
            framework=self.framework, name='Cambridge Lower Secondary', academic_option=self.option, order=1,
        )
        self.matching_grade = GradeLevel.objects.create(name='Year 7 (Grade 6)', order=7, year_level=self.year_level)
        GradeLevelTrackMapping.objects.create(
            year_level=self.year_level, track=self.track, is_enabled=True, custom_label='Year 7',
        )
        self.unmatched_grade = GradeLevel.objects.create(name='K1-IC', order=0)
        self.guardian = Guardian.objects.create(full_name='Jordan Roe')

    def test_groups_real_grade_levels_under_their_track(self):
        response = self.client.get('/api/v1/roster-filter-options/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group = next(g for g in response.data['groups'] if g['track'] == 'Cambridge Lower Secondary')
        self.assertEqual([g['id'] for g in group['grade_levels']], [self.matching_grade.id])
        self.assertEqual([g['id'] for g in response.data['ungrouped']], [self.unmatched_grade.id])

    def test_disabled_academic_option_hides_track_from_roster_filters(self):
        self.option.is_enabled = False
        self.option.save(update_fields=['is_enabled'])
        response = self.client.get('/api/v1/roster-filter-options/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.track.name, [group['track'] for group in response.data['groups']])

    def test_add_user_options_include_only_assignable_grades_and_parent_choices(self):
        AcademicYear.objects.create(name='2026-2027', is_current=True)
        response = self.client.get('/api/v1/roster-user-options/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([grade['id'] for grade in response.data['grade_levels']], [self.matching_grade.id])
        self.assertEqual(response.data['parents'], [{'id': self.guardian.id, 'full_name': 'Jordan Roe'}])
        self.assertTrue(response.data['parents_enabled'])

