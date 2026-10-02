from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration, AcademicYear, ClassRoom, GradeLevel, Programme
from accounts.models import User


class ClassRoomConfigurationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='classes-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)
        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.grade = GradeLevel.objects.create(name='Year 12', order=12)
        configuration = AcademicConfiguration.load()
        configuration.classes_enabled = False
        configuration.save(update_fields=['classes_enabled'])

    def test_classes_setting_blocks_non_dp_but_allows_dp_and_preserves_read_access(self):
        programme = Programme.objects.create(name='Integrated Curriculum')
        dp = Programme.objects.create(name='DP')
        base_payload = {
            'academic_year': self.year.id,
            'grade_level': self.grade.id,
            'english_name': '12A',
            'khmer_name': '',
        }
        blocked = self.client.post('/api/v1/classrooms/', {
            **base_payload,
            'programme': programme.id,
        }, format='json')
        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)

        allowed = self.client.post('/api/v1/classrooms/', {
            **base_payload,
            'programme': dp.id,
        }, format='json')
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.get('/api/v1/classrooms/').status_code, status.HTTP_200_OK)
        with self.assertRaises(ValidationError):
            ClassRoom(
                academic_year=self.year,
                grade_level=self.grade,
                programme=programme,
                english_name='12B',
            ).full_clean()
        with self.assertRaises(ValidationError):
            ClassRoom(
                academic_year=self.year,
                grade_level=self.grade,
                english_name='12C',
            ).full_clean()

