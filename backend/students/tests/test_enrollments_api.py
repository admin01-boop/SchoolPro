from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import (
    AcademicCurriculumOption,
    AcademicYear,
    Curriculum,
    CurriculumFramework,
    CurriculumTrack,
    GradeLevel,
    GradeLevelTrackMapping,
    YearLevel,
)
from accounts.models import User
from students.models import Student


class EnrollmentGradeLevelGatingTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.student = Student.objects.create(
            student_id='S1', full_name='Test Student', sex=Student.Sex.MALE, date_of_birth=date(2014, 1, 1),
        )

        year_level = YearLevel.objects.create(name='Year 7', order=7)
        framework = CurriculumFramework.objects.create(name='Cambridge', order=1)
        option = AcademicCurriculumOption.objects.create(
            code='test-enrollment-lower-secondary', provider='Cambridge',
            name='Lower Secondary', is_enabled=True,
        )
        track = CurriculumTrack.objects.create(
            framework=framework, name='Lower Secondary', academic_option=option, order=1,
        )
        self.enabled_grade = GradeLevel.objects.create(name='Year 7 (Grade 6)', order=7, year_level=year_level)
        GradeLevelTrackMapping.objects.create(
            year_level=year_level, track=track, is_enabled=True, custom_label='Different display label',
        )
        self.disabled_grade = GradeLevel.objects.create(name='Year 20 (Unused)', order=20)

    def _payload(self, grade_level_id):
        return {
            'student': self.student.id, 'academic_year': self.year.id, 'grade_level': grade_level_id,
            'enrollment_status': 'NEW', 'start_date': '2026-09-01',
        }

    def test_create_with_enabled_grade_level_succeeds(self):
        response = self.client.post('/api/v1/enrollments/', self._payload(self.enabled_grade.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_non_enabled_grade_level_rejected(self):
        response = self.client.post('/api/v1/enrollments/', self._payload(self.disabled_grade.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('grade_level', response.data)

    def test_create_with_no_grade_level_allowed(self):
        response = self.client.post('/api/v1/enrollments/', self._payload(None), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_disabled_curriculum_rejected(self):
        option = AcademicCurriculumOption.objects.create(
            code='disabled-test-curriculum', provider='Test', name='Disabled Curriculum', is_enabled=False,
        )
        curriculum = Curriculum.objects.create(name='Disabled Curriculum')
        curriculum.academic_options.add(option)
        payload = self._payload(self.enabled_grade.id)
        payload['curriculum'] = curriculum.id

        response = self.client.post('/api/v1/enrollments/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('curriculum', response.data)

