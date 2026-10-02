from datetime import date

from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from students.models import Student


class TeacherProfileTests(TestCase):
    def test_creating_a_teacher_account_creates_a_teacher_profile(self):
        staff = User.objects.create_user(username='creator', password='Str0ngPass!23', role=User.Role.STAFF)
        client = APIClient()
        client.force_authenticate(staff)

        response = client.post('/api/v1/roster-users/', {
            'user_type': User.Role.TEACHER,
            'first_name': 'Taylor',
            'last_name': 'Advisor',
            'email': 'taylor@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.get(id=response.data['id']).teacher_profile)

    def test_creating_a_staff_account_creates_a_staff_profile(self):
        creator = User.objects.create_user(username='creator2', password='Str0ngPass!23', role=User.Role.STAFF)
        client = APIClient()
        client.force_authenticate(creator)

        response = client.post('/api/v1/roster-users/', {
            'user_type': User.Role.STAFF,
            'first_name': 'Sam',
            'last_name': 'Clerk',
            'email': 'sam@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.get(id=response.data['id']).staff_profile)

    def test_creating_an_observer_account_creates_an_observer_profile(self):
        creator = User.objects.create_user(username='creator3', password='Str0ngPass!23', role=User.Role.STAFF)
        client = APIClient()
        client.force_authenticate(creator)

        response = client.post('/api/v1/roster-users/', {
            'user_type': User.Role.OBSERVER,
            'first_name': 'Olive',
            'last_name': 'Watcher',
            'email': 'olive@example.com',
            'send_welcome_email': False,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.get(id=response.data['id']).observer_profile)


class AuditTrailTests(TestCase):
    def test_api_changes_record_the_acting_user(self):
        staff = User.objects.create_user(username='auditor', password='Str0ngPass!23', role=User.Role.STAFF)
        token = Token.objects.create(user=staff)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.post('/api/v1/students/', {
            'student_id': 'A1', 'full_name': 'Audit Student', 'sex': Student.Sex.FEMALE,
            'date_of_birth': date(2014, 1, 1).isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        record = Student.history.get(student_id='A1')
        self.assertEqual(record.history_user, staff)
        self.assertEqual(record.history_type, '+')

    def test_user_history_never_stores_password_hashes(self):
        User.objects.create_user(username='someone', password='Str0ngPass!23')
        self.assertFalse(hasattr(User.history.first(), 'password'))
