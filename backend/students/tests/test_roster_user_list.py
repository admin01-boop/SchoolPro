from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from staff.models import AdminProfile, Observer, StaffMember, Teacher
from students.models import Guardian, Student, StudentGuardian


class RosterAdminListTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='list-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(staff)

    def test_admins_come_from_admin_table(self):
        user = User.objects.create_user(
            username='a1', first_name='Adam', last_name='Ng', email='adam@example.com', role=User.Role.ADMIN,
        )
        AdminProfile.objects.filter(user=user).update(employee_id='A-1', job_title='Principal', phone='012')
        User.objects.create_user(username='a2', role=User.Role.ADMIN, first_name='Other')

        response = self.client.get('/api/v1/roster-admins/?search=principal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual((row['full_name'], row['job_title'], row['employee_id']), ('Adam Ng', 'Principal', 'A-1'))

    def test_non_staff_forbidden(self):
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username='p2', role=User.Role.PARENT))
        for path in (
            'roster-admins/', 'roster-teachers/', 'roster-staff/', 'roster-observers/', 'roster-parents/',
        ):
            self.assertEqual(client.get(f'/api/v1/{path}').status_code, status.HTTP_403_FORBIDDEN, path)


class RosterTeacherParentListTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='list-staff2', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(staff)

    def test_teachers_come_from_teacher_table(self):
        user = User.objects.create_user(
            username='t1', first_name='Tara', last_name='Lee', email='tara@example.com', role=User.Role.TEACHER,
        )
        Teacher.objects.filter(user=user).update(employee_id='E1')
        User.objects.create_user(username='t2', role=User.Role.TEACHER, first_name='Other')

        response = self.client.get('/api/v1/roster-teachers/?search=tara')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual((row['full_name'], row['email'], row['employee_id']), ('Tara Lee', 'tara@example.com', 'E1'))

    def test_staff_come_from_staff_table(self):
        user = User.objects.create_user(
            username='s1', first_name='Sam', last_name='Clerk', email='sam@example.com', role=User.Role.STAFF,
        )
        StaffMember.objects.filter(user=user).update(employee_id='S-1', job_title='Registrar', department='Office')
        User.objects.create_user(username='s2', role=User.Role.STAFF, first_name='Other')

        response = self.client.get('/api/v1/roster-staff/?search=registrar')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual(
            (row['full_name'], row['job_title'], row['department']), ('Sam Clerk', 'Registrar', 'Office'),
        )

    def test_observers_come_from_observer_table(self):
        user = User.objects.create_user(
            username='ob1', first_name='Olga', last_name='Lee', email='olga@example.com', role=User.Role.OBSERVER,
        )
        Observer.objects.filter(user=user).update(organization='Ministry', phone='012')
        User.objects.create_user(username='ob2', role=User.Role.OBSERVER, first_name='Other')

        response = self.client.get('/api/v1/roster-observers/?search=ministry')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual((row['full_name'], row['organization'], row['phone']), ('Olga Lee', 'Ministry', '012'))

    def test_parents_include_guardians_without_login(self):
        student = Student.objects.create(
            student_id='S1', full_name='Kid Roe', sex=Student.Sex.MALE, date_of_birth='2014-01-01',
        )
        no_login = Guardian.objects.create(full_name='Imported Parent', phone_1='012')
        StudentGuardian.objects.create(student=student, guardian=no_login, relationship='MOTHER')
        login_user = User.objects.create_user(username='p1', email='p@example.com', role=User.Role.PARENT)
        Guardian.objects.create(full_name='Login Parent', user=login_user)

        response = self.client.get('/api/v1/roster-parents/')
        self.assertEqual(response.data['count'], 2)
        by_name = {row['full_name']: row for row in response.data['results']}
        self.assertFalse(by_name['Imported Parent']['has_login'])
        self.assertEqual(by_name['Imported Parent']['children'][0]['full_name'], 'Kid Roe')
        self.assertTrue(by_name['Login Parent']['has_login'])
        self.assertEqual(by_name['Login Parent']['email'], 'p@example.com')
