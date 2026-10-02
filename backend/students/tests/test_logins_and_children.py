import os
import tempfile

from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration
from accounts.models import User
from staff.models import Teacher
from students.models import Guardian, Student, StudentGuardian


class CreateStudentLoginsTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            student_id='S1', full_name='Kid Roe', sex='MALE', date_of_birth='2014-01-01',
        )
        self.output = os.path.join(tempfile.mkdtemp(), 'logins.csv')

    def test_creates_login_and_is_safe_to_rerun(self):
        call_command('create_student_logins', domain='school.edu', output=self.output, stdout=open(os.devnull, 'w'))

        self.student.refresh_from_db()
        self.assertEqual(self.student.user.username, 's1@school.edu')
        self.assertEqual(self.student.user.role, User.Role.STUDENT)
        self.assertTrue(self.student.user.has_usable_password())

        call_command('create_student_logins', domain='school.edu', output=self.output, stdout=open(os.devnull, 'w'))
        self.assertEqual(User.objects.filter(role=User.Role.STUDENT).count(), 1)

    def test_dry_run_changes_nothing(self):
        call_command('create_student_logins', domain='school.edu', output=self.output, dry_run=True,
                     stdout=open(os.devnull, 'w'))

        self.student.refresh_from_db()
        self.assertIsNone(self.student.user)
        self.assertFalse(os.path.exists(self.output))


class UsernameFollowsEmailTests(TestCase):
    def test_editing_email_updates_username(self):
        staff = User.objects.create_user(username='editor', role=User.Role.STAFF)
        user = User.objects.create_user(username='t1@school.edu', email='t1@school.edu', role=User.Role.TEACHER)
        teacher = Teacher.objects.get(user=user)
        client = APIClient()
        client.force_authenticate(staff)

        response = client.patch(
            f'/api/v1/roster-teachers/{teacher.id}/',
            {'first_name': 'T', 'last_name': 'One', 'email': 'New.T1@school.edu'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        user.refresh_from_db()
        self.assertEqual(user.username, 'new.t1@school.edu')

    def test_email_already_used_is_rejected(self):
        staff = User.objects.create_user(username='editor', role=User.Role.STAFF)
        User.objects.create_user(username='taken@school.edu', role=User.Role.TEACHER)
        user = User.objects.create_user(username='t2@school.edu', role=User.Role.TEACHER)
        client = APIClient()
        client.force_authenticate(staff)

        response = client.patch(
            f'/api/v1/roster-teachers/{Teacher.objects.get(user=user).id}/',
            {'first_name': 'T', 'last_name': 'Two', 'email': 'taken@school.edu'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MyChildrenTests(TestCase):
    def setUp(self):
        config = AcademicConfiguration.load()
        config.parents_association_enabled = True
        config.save()
        self.parent = User.objects.create_user(username='p@school.edu', role=User.Role.PARENT)
        guardian = Guardian.objects.create(full_name='Mum Roe', user=self.parent)
        self.kid = Student.objects.create(student_id='S1', full_name='Kid Roe', sex='MALE', date_of_birth='2014-01-01')
        Student.objects.create(student_id='S2', full_name='Other Kid', sex='MALE', date_of_birth='2014-01-01')
        StudentGuardian.objects.create(student=self.kid, guardian=guardian, relationship='MOTHER')

    def test_parent_sees_only_own_children(self):
        client = APIClient()
        client.force_authenticate(self.parent)

        response = client.get('/api/v1/me/children/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([child['full_name'] for child in response.json()], ['Kid Roe'])

    def test_non_parent_is_forbidden(self):
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username='s@school.edu', role=User.Role.STUDENT))

        self.assertEqual(client.get('/api/v1/me/children/').status_code, status.HTTP_403_FORBIDDEN)
