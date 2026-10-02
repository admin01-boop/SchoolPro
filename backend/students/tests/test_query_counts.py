from datetime import date

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from academics.models import AcademicYear, GradeLevel
from accounts.models import User
from students.models import Enrollment, Guardian, Student, StudentGuardian


class StudentListQueryCountTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='perf-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(staff)
        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        self.grade = GradeLevel.objects.create(name='Year 7', order=7)

    def _add_student(self, number):
        student = Student.objects.create(
            student_id=f'P{number}', full_name=f'Student {number}', sex=Student.Sex.FEMALE,
            date_of_birth=date(2014, 1, 1),
        )
        Enrollment.objects.create(
            student=student, academic_year=self.year, grade_level=self.grade,
            enrollment_status=Enrollment.Status.NEW, start_date=date(2026, 9, 1),
        )
        guardian = Guardian.objects.create(full_name=f'Guardian {number}')
        StudentGuardian.objects.create(
            student=student, guardian=guardian, relationship=StudentGuardian.Relationship.OTHER,
        )

    def _list_query_count(self):
        with CaptureQueriesContext(connection) as context:
            response = self.client.get('/api/v1/students/')
        self.assertEqual(response.status_code, 200)
        return len(context)

    def test_list_query_count_does_not_grow_with_rows(self):
        self._add_student(1)
        few = self._list_query_count()
        for number in range(2, 12):
            self._add_student(number)
        self.assertEqual(self._list_query_count(), few)
