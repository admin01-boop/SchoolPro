from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration, AcademicYear
from accounts.models import User
from students.models import Enrollment, Guardian, Student, StudentGuardian

URL = '/api/v1/me/student/'


def _student(student_id, user=None, full_name='Kid Roe'):
    return Student.objects.create(
        student_id=student_id, full_name=full_name, sex=Student.Sex.FEMALE,
        date_of_birth=date(2014, 1, 1), remark='staff-only note', user=user,
    )


class MyStudentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='kid', password='Str0ngPass!23', role=User.Role.STUDENT)
        self.student = _student('S1', user=self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_student_gets_only_their_own_record(self):
        _student('S2', full_name='Someone Else')

        response = self.client.get(URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual((response.data['student_id'], response.data['full_name']), ('S1', 'Kid Roe'))

    def test_staff_only_fields_are_not_exposed(self):
        response = self.client.get(URL)
        self.assertNotIn('remark', response.data)
        self.assertNotIn('id', response.data)

    def test_current_enrollment_status_is_shown(self):
        year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        Enrollment.objects.create(
            student=self.student, academic_year=year, enrollment_status=Enrollment.Status.EXISTING,
            start_date=date(2026, 9, 1),
        )

        response = self.client.get(URL)

        self.assertEqual(response.data['enrollment_status'], 'Existing')

    def test_guardians_are_listed_when_parents_association_is_enabled(self):
        config = AcademicConfiguration.load()
        config.parents_association_enabled = True
        config.save()
        guardian = Guardian.objects.create(full_name='Mum Roe')
        StudentGuardian.objects.create(student=self.student, guardian=guardian, relationship='MOTHER')

        response = self.client.get(URL)

        self.assertEqual(response.data['guardians'], [{'full_name': 'Mum Roe', 'relationship': 'Mother'}])

    def test_guardians_are_hidden_when_parents_association_is_disabled(self):
        config = AcademicConfiguration.load()
        config.parents_association_enabled = False
        config.save()
        guardian = Guardian.objects.create(full_name='Mum Roe')
        StudentGuardian.objects.create(student=self.student, guardian=guardian, relationship='MOTHER')

        response = self.client.get(URL)

        self.assertEqual(response.data['guardians'], [])

    def test_student_without_a_linked_record_gets_404(self):
        lonely = User.objects.create_user(username='lonely', role=User.Role.STUDENT)
        client = APIClient()
        client.force_authenticate(lonely)

        self.assertEqual(client.get(URL).status_code, status.HTTP_404_NOT_FOUND)

    def test_other_roles_are_forbidden(self):
        for role in (User.Role.STAFF, User.Role.ADMIN, User.Role.TEACHER, User.Role.PARENT, User.Role.OBSERVER):
            client = APIClient()
            client.force_authenticate(User.objects.create_user(username=f'u-{role}', role=role))
            self.assertEqual(client.get(URL).status_code, status.HTTP_403_FORBIDDEN, role)

    def test_unauthenticated_is_rejected(self):
        response = APIClient().get(URL)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_student_cannot_use_management_endpoints(self):
        for path in ('/api/v1/students/', '/api/v1/roster-teachers/', '/api/v1/guardians/'):
            self.assertEqual(self.client.get(path).status_code, status.HTTP_403_FORBIDDEN, path)

    def test_student_cannot_modify_via_the_portal_endpoint(self):
        self.assertEqual(
            self.client.patch(URL, {'full_name': 'Hacked'}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
