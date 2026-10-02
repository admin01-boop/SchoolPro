from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import (
    AcademicConfiguration,
    AcademicCurriculumOption,
    Curriculum,
    CurriculumTrack,
    GradeLevelTrackMapping,
    YearLevel,
)
from accounts.models import User


class KeyAcademicFunctionsViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='academic-settings-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

    def test_get_returns_seeded_options_and_school_defaults(self):
        response = self.client.get('/api/v1/key-academic-functions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['curricula']), 19)
        self.assertTrue(response.data['configuration']['classes_enabled'])
        self.assertEqual(response.data['configuration']['term_grade_calculation'], 'PERCENTAGE')
        self.assertEqual(
            next(option for option in response.data['curricula'] if option['code'] == 'national-high-school')['short_name'],
            'HS',
        )

    def test_put_persists_configuration_and_curriculum_selections(self):
        ib_diploma = AcademicCurriculumOption.objects.get(code='ib-diploma')
        high_school = AcademicCurriculumOption.objects.get(code='national-high-school')
        response = self.client.put('/api/v1/key-academic-functions/', {
            'configuration': {
                'classes_enabled': False,
                'parents_association_enabled': True,
                'annotations_enabled': False,
                'term_grade_calculation': 'ABSOLUTE',
                'points_based_averaging': False,
                'year_level_behaviour': 'PRESERVE',
            },
            'curricula': [
                {'id': ib_diploma.id, 'is_enabled': True},
                {'id': high_school.id, 'is_enabled': True, 'short_name': 'HSX', 'full_title': 'Senior School'},
            ],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = AcademicConfiguration.objects.get(pk=1)
        self.assertFalse(settings.classes_enabled)
        self.assertEqual(settings.term_grade_calculation, 'ABSOLUTE')
        self.assertFalse(settings.points_based_averaging)
        ib_diploma.refresh_from_db()
        high_school.refresh_from_db()
        self.assertTrue(ib_diploma.is_enabled)
        self.assertTrue(high_school.is_enabled)
        self.assertEqual(high_school.short_name, 'HSX')
        self.assertEqual(high_school.full_title, 'Senior School')

    def test_enabling_new_option_creates_linked_track_and_curriculum(self):
        option = AcademicCurriculumOption.objects.get(code='pearson-btec')
        configuration = AcademicConfiguration.load()
        from academics.api.serializers import AcademicConfigurationSerializer

        response = self.client.put('/api/v1/key-academic-functions/', {
            'configuration': AcademicConfigurationSerializer(configuration).data,
            'curricula': [{'id': option.id, 'is_enabled': True}],
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        option.refresh_from_db()
        track = CurriculumTrack.objects.get(academic_option=option)
        curriculum = Curriculum.objects.get(academic_options=option)
        self.assertEqual(track.name, option.name)
        self.assertEqual(track.framework.name, option.provider)
        self.assertEqual(curriculum.name, option.name)
        self.assertEqual(
            GradeLevelTrackMapping.objects.filter(track=track).count(),
            YearLevel.objects.count(),
        )
        self.assertFalse(GradeLevelTrackMapping.objects.filter(track=track, is_enabled=True).exists())

    def test_curriculum_endpoint_hides_records_with_disabled_options(self):
        option = AcademicCurriculumOption.objects.get(code='ib-diploma')
        option.is_enabled = False
        option.save(update_fields=['is_enabled'])
        curriculum = Curriculum.objects.get(name='IB Diploma')
        curriculum.academic_options.add(option)

        response = self.client.get('/api/v1/curriculums/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('IB Diploma', [row['name'] for row in response.data['results']])

    def test_requires_staff_role(self):
        parent = User.objects.create_user(username='academic-settings-parent', password='Str0ngPass!23', role=User.Role.PARENT)
        self.client.force_authenticate(parent)
        response = self.client.get('/api/v1/key-academic-functions/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

