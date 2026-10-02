from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
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
from students.models import Enrollment, Guardian, Student, StudentGuardian


class RosterUserCreateTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='roster-create-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(staff)
        self.year = AcademicYear.objects.create(name='2026-2027', is_current=True)
        year_level = YearLevel.objects.create(name='Year 7', order=7)
        framework = CurriculumFramework.objects.create(name='Roster Create Framework', order=1)
        option = AcademicCurriculumOption.objects.create(
            code='roster-create-option', provider='Roster Create', name='Roster Create Track', is_enabled=True,
        )
        track = CurriculumTrack.objects.create(
            framework=framework, name='Roster Create Track', academic_option=option, order=1,
        )
        self.grade = GradeLevel.objects.create(name='Year 7', order=7, year_level=year_level)
        GradeLevelTrackMapping.objects.create(year_level=year_level, track=track, is_enabled=True)
        self.guardian = Guardian.objects.create(full_name='Jordan Roe')

    def _student_payload(self, **overrides):
        payload = {
            'user_type': User.Role.STUDENT,
            'first_name': 'Casey',
            'last_name': 'Roe',
            'email': 'casey.roe@example.com',
            'ui_language': User.Language.ENGLISH,
            'student_id': 'S200',
            'sex': Student.Sex.FEMALE,
            'date_of_birth': '2014-05-01',
            'grade_level': self.grade.id,
            'parent_ids': [self.guardian.id],
            'send_welcome_email': False,
        }
        payload.update(overrides)
        return payload

    def test_create_student_account_enrollment_and_parent_links(self):
        response = self.client.post('/api/v1/roster-users/', self._student_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(id=response.data['id'])
        student = Student.objects.get(user=user)
        enrollment = Enrollment.objects.get(student=student, academic_year=self.year)
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertEqual(user.ui_language, User.Language.ENGLISH)
        self.assertEqual(student.student_id, 'S200')
        self.assertEqual(enrollment.grade_level, self.grade)
        self.assertTrue(StudentGuardian.objects.filter(
            student=student, guardian=self.guardian, relationship=StudentGuardian.Relationship.OTHER,
        ).exists())
        self.assertTrue(user.check_password(response.data['initial_password']))

    def test_create_non_student_role_without_student_profile(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.TEACHER,
            'first_name': 'Taylor',
            'last_name': 'Advisor',
            'email': 'taylor@example.com',
            'ui_language': User.Language.KHMER,
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(id=response.data['id'])
        self.assertEqual(user.role, User.Role.TEACHER)
        self.assertEqual(user.ui_language, User.Language.KHMER)
        self.assertFalse(Student.objects.filter(user=user).exists())

    @override_settings(MAILERS={
        'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'},
    })
    def test_console_mailer_falls_back_to_returning_the_initial_password(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.TEACHER,
            'first_name': 'Taylor',
            'last_name': 'Advisor',
            'email': 'taylor.console@example.com',
            'send_welcome_email': True,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertFalse(response.data['welcome_email_sent'])
        self.assertTrue(response.data['initial_password'])
        self.assertEqual(mail.outbox, [])

    @override_settings(MAILERS={
        'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'},
    })
    def test_configured_mailer_sends_welcome_email_and_withholds_password_response(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.TEACHER,
            'first_name': 'Taylor',
            'last_name': 'Advisor',
            'email': 'taylor.email@example.com',
            'send_welcome_email': True,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(response.data['welcome_email_sent'])
        self.assertNotIn('initial_password', response.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['taylor.email@example.com'])
        self.assertIn(response.data['username'], mail.outbox[0].body)
        password = mail.outbox[0].body.split('temporary password is ', 1)[1].split('. Sign in', 1)[0]
        self.assertTrue(User.objects.get(id=response.data['id']).check_password(password))

    @override_settings(MAILERS={
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {'host': 'smtp.example.com', 'port': 587, 'use_tls': True},
        },
    })
    @patch('students.services.send_mail', return_value=1)
    def test_smtp_mailer_with_host_is_treated_as_configured(self, send_mail_mock):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.TEACHER,
            'first_name': 'Taylor',
            'last_name': 'Advisor',
            'email': 'taylor.smtp@example.com',
            'send_welcome_email': True,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(response.data['welcome_email_sent'])
        self.assertNotIn('initial_password', response.data)
        send_mail_mock.assert_called_once()

    def test_create_parent_role_with_guardian_profile(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.PARENT,
            'first_name': 'Morgan',
            'last_name': 'Roe',
            'email': 'morgan@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(id=response.data['id'])
        self.assertTrue(Guardian.objects.filter(user=user, full_name='Morgan Roe').exists())

    def test_superuser_can_create_an_admin_account(self):
        superuser = User.objects.create_superuser(
            username='roster-superuser', email='root@example.com', password='Str0ngPass!23',
        )
        client = APIClient()
        client.force_authenticate(superuser)

        response = client.post('/api/v1/roster-users/', {
            'user_type': User.Role.ADMIN,
            'first_name': 'New',
            'last_name': 'Admin',
            'email': 'admin.new@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(User.objects.get(id=response.data['id']).role, User.Role.ADMIN)

    def test_student_creation_requires_student_model_fields(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.STUDENT,
            'first_name': 'Incomplete',
            'last_name': 'Student',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_grade_assignment_requires_a_current_academic_year(self):
        self.year.is_current = False
        self.year.save(update_fields=['is_current'])

        response = self.client.post('/api/v1/roster-users/', self._student_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current academic year', str(response.data['grade_level'][0]))
        self.assertEqual(User.objects.count(), 1)

    def test_staff_cannot_create_an_admin_account(self):
        response = self.client.post('/api/v1/roster-users/', {
            'user_type': User.Role.ADMIN,
            'first_name': 'New',
            'last_name': 'Admin',
            'email': 'admin.new@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.count(), 1)

