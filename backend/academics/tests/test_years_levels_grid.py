from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.grade_matching import assignable_grade_level_ids
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


class YearsLevelsGridViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

        self.academic_year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.year_level = YearLevel.objects.create(name='Year 1', order=1)
        self.framework = CurriculumFramework.objects.create(name='Cambridge', order=1)
        self.option = AcademicCurriculumOption.objects.create(
            code='test-grid-igcse', provider='Cambridge', name='IGCSE', is_enabled=True,
        )
        self.track = CurriculumTrack.objects.create(
            framework=self.framework, name='IGCSE', academic_option=self.option, order=1,
        )

    def test_get_returns_grid_shape(self):
        response = self.client.get('/api/v1/years-levels-grid/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('year_levels', response.data)
        self.assertIn('frameworks', response.data)
        self.assertIn('mappings', response.data)
        self.assertEqual(response.data['selected_academic_year'], self.academic_year.id)
        self.assertEqual(
            len(response.data['mappings']),
            len(response.data['year_levels']) * sum(len(framework['tracks']) for framework in response.data['frameworks']),
        )

    def test_inactive_tracks_are_hidden_from_grid(self):
        option = AcademicCurriculumOption.objects.get(code='pearson-btec')
        option.is_enabled = False
        option.save(update_fields=['is_enabled'])
        inactive_track = CurriculumTrack.objects.get(academic_option=option)

        response = self.client.get('/api/v1/years-levels-grid/')
        self.assertNotIn('Pearson Edexcel', [group['name'] for group in response.data['frameworks']])
        self.assertNotIn(f'{self.year_level.id}:{inactive_track.id}', response.data['mappings'])

    def test_format_and_labels_are_scoped_to_selected_academic_year(self):
        next_year = AcademicYear.objects.create(
            name='2027-2028', grade_numbering_format=AcademicYear.NumberingFormat.GRADE_11_12,
        )
        year_12 = YearLevel.objects.create(name='Year 12', order=12)
        GradeLevel.objects.create(name='Year 12 (Grade 11)', order=12, year_level=year_12)

        grid = self.client.get('/api/v1/years-levels-grid/', {'academic_year': next_year.id})
        self.assertEqual(grid.data['grade_numbering_format'], AcademicYear.NumberingFormat.GRADE_11_12)
        year_12 = next(row for row in grid.data['year_levels'] if row['name'] == 'Year 12')
        self.assertEqual(year_12['grade_display_name'], 'Grade 11')

        grade_levels = self.client.get('/api/v1/grade-levels/', {'academic_year': next_year.id})
        grade = next(row for row in grade_levels.data['results'] if row['name'] == 'Year 12 (Grade 11)')
        self.assertEqual(grade['display_name'], 'Grade 11')

    def test_put_saves_mapping_and_updates_in_place(self):
        payload = {
            'academic_year': self.academic_year.id,
            'grade_numbering_format': 'YEAR_12_13',
            'mappings': [
                {'year_level': self.year_level.id, 'track': self.track.id, 'is_enabled': True, 'custom_label': 'Year 1'},
            ],
        }
        response = self.client.put('/api/v1/years-levels-grid/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mapping = GradeLevelTrackMapping.objects.get(year_level=self.year_level, track=self.track)
        self.assertTrue(mapping.is_enabled)
        self.assertEqual(mapping.custom_label, 'Year 1')

        # Saving again must update the existing row, not create a duplicate.
        payload['mappings'][0]['is_enabled'] = False
        response = self.client.put('/api/v1/years-levels-grid/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GradeLevelTrackMapping.objects.count(), 1)
        mapping.refresh_from_db()
        self.assertFalse(mapping.is_enabled)

    def test_disabled_curriculum_track_is_hidden_and_cannot_be_reenabled_through_grid_save(self):
        option = AcademicCurriculumOption.objects.get(code='cambridge-igcse')
        option.is_enabled = False
        option.save(update_fields=['is_enabled'])
        track = CurriculumTrack.objects.get(academic_option=option)
        GradeLevel.objects.create(name='Configured inactive grade', order=1, year_level=self.year_level)

        response = self.client.put('/api/v1/years-levels-grid/', {
            'academic_year': self.academic_year.id,
            'grade_numbering_format': 'YEAR_12_13',
            'mappings': [{
                'year_level': self.year_level.id,
                'track': track.id,
                'is_enabled': True,
                'custom_label': 'Year 1',
            }],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(GradeLevelTrackMapping.objects.filter(year_level=self.year_level, track=track).exists())

    def test_checkbox_enables_all_grades_linked_to_the_standard_row(self):
        grade = GradeLevel.objects.create(name='Year 1 (K3)', order=1, year_level=self.year_level)
        variant = GradeLevel.objects.create(name='Year 1-IC', order=1, year_level=self.year_level)
        payload = {
            'academic_year': self.academic_year.id,
            'grade_numbering_format': 'YEAR_12_13',
            'mappings': [
                {'year_level': self.year_level.id, 'track': self.track.id, 'is_enabled': True, 'custom_label': 'User alias'},
            ],
        }
        response = self.client.put('/api/v1/years-levels-grid/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reconciliation']['linked'], 1)
        mapping = GradeLevelTrackMapping.objects.get(year_level=self.year_level, track=self.track)
        self.assertEqual(mapping.custom_label, 'User alias')
        self.assertNotIn('grade_level', response.data.get('mappings', {}).get(f'{self.year_level.id}:{self.track.id}', {}))
        self.assertEqual(assignable_grade_level_ids(), {grade.id, variant.id})

    def test_requires_staff_role(self):
        parent = User.objects.create_user(username='parent1', password='Str0ngPass!23', role=User.Role.PARENT)
        client = APIClient()
        client.force_authenticate(parent)
        response = client.get('/api/v1/years-levels-grid/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

