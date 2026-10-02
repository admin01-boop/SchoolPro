from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration
from accounts.models import User
from staff.models import AdminProfile, Observer, StaffMember, Teacher
from students.models import Guardian, Student

PROFILE_BY_ROLE = {
    User.Role.TEACHER: Teacher,
    User.Role.STAFF: StaffMember,
    User.Role.OBSERVER: Observer,
    User.Role.ADMIN: AdminProfile,
}


class RoleProfileCreationTests(TestCase):
    def test_every_creation_path_gets_a_profile_for_its_role(self):
        for role, model in PROFILE_BY_ROLE.items():
            user = User.objects.create_user(username=f'u-{role}', role=role)
            self.assertTrue(model.objects.filter(user=user).exists(), role)

    def test_saving_a_user_again_does_not_duplicate_the_profile(self):
        user = User.objects.create_user(username='t1', role=User.Role.TEACHER)
        user.first_name = 'Tara'
        user.save()
        self.assertEqual(Teacher.objects.filter(user=user).count(), 1)

    def test_student_and_parent_users_get_no_staff_app_profile(self):
        for role in (User.Role.STUDENT, User.Role.PARENT):
            user = User.objects.create_user(username=f'u-{role}', role=role)
            self.assertFalse(any(model.objects.filter(user=user).exists() for model in PROFILE_BY_ROLE.values()))

    def test_default_role_grants_no_management_access(self):
        user = User.objects.create_user(username='nobody')
        self.assertEqual(user.role, User.Role.OBSERVER)

    def test_createsuperuser_defaults_to_admin_with_profile(self):
        user = User.objects.create_superuser(username='root', email='r@example.com', password='Str0ngPass!23')
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(AdminProfile.objects.filter(user=user).exists())

    def test_manage_command_createsuperuser_uses_admin_role(self):
        call_command('createsuperuser', interactive=False, username='cli-root', email='c@example.com')
        self.assertEqual(User.objects.get(username='cli-root').role, User.Role.ADMIN)


class RosterProfileEditTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(username='editor', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(self.staff_user)

    def test_patch_updates_profile_and_login_user(self):
        user = User.objects.create_user(username='t1', first_name='Tara', last_name='Lee', role=User.Role.TEACHER)
        profile = user.teacher_profile

        response = self.client.patch(f'/api/v1/roster-teachers/{profile.id}/', {
            'first_name': 'Tarah', 'email': 'tarah@example.com', 'employee_id': 'E9', 'hire_date': '2024-08-01',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name, user.email), ('Tarah', 'Lee', 'tarah@example.com'))
        self.assertEqual((profile.employee_id, str(profile.hire_date)), ('E9', '2024-08-01'))
        self.assertEqual(response.data['full_name'], 'Tarah Lee')

    def test_each_profile_endpoint_edits_its_own_fields(self):
        cases = [
            ('roster-staff', User.Role.STAFF, 'staff_profile', {'job_title': 'Registrar', 'department': 'Office'}),
            ('roster-observers', User.Role.OBSERVER, 'observer_profile', {'organization': 'Ministry', 'phone': '012'}),
        ]
        for path, role, related_name, payload in cases:
            profile = getattr(User.objects.create_user(username=f'x-{role}', role=role), related_name)
            response = self.client.patch(f'/api/v1/{path}/{profile.id}/', payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            for field, value in payload.items():
                self.assertEqual(response.data[field], value)

    def test_blank_employee_id_is_stored_as_null_so_it_does_not_collide(self):
        first = User.objects.create_user(username='t1', role=User.Role.TEACHER).teacher_profile
        second = User.objects.create_user(username='t2', role=User.Role.TEACHER).teacher_profile
        for profile in (first, second):
            response = self.client.patch(f'/api/v1/roster-teachers/{profile.id}/', {'employee_id': ''}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            profile.refresh_from_db()
            self.assertIsNone(profile.employee_id)

    def test_duplicate_employee_id_is_rejected(self):
        first = User.objects.create_user(username='t1', role=User.Role.TEACHER).teacher_profile
        second = User.objects.create_user(username='t2', role=User.Role.TEACHER).teacher_profile
        self.client.patch(f'/api/v1/roster-teachers/{first.id}/', {'employee_id': 'E1'}, format='json')

        response = self.client.patch(f'/api/v1/roster-teachers/{second.id}/', {'employee_id': 'E1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_role_cannot_edit_an_admin_profile(self):
        profile = User.objects.create_user(username='a1', role=User.Role.ADMIN).admin_profile

        response = self.client.patch(f'/api/v1/roster-admins/{profile.id}/', {'job_title': 'X'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        profile.refresh_from_db()
        self.assertEqual(profile.job_title, '')

    def test_admin_can_edit_an_admin_profile(self):
        admin_client = APIClient()
        admin_user = User.objects.create_user(username='boss', role=User.Role.ADMIN)
        admin_client.force_authenticate(admin_user)
        profile = User.objects.create_user(username='a1', role=User.Role.ADMIN).admin_profile

        response = admin_client.patch(f'/api/v1/roster-admins/{profile.id}/', {'job_title': 'Principal'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

    def test_only_admin_can_reset_password_and_require_change_at_login(self):
        user = User.objects.create_user(username='t1', password='Original-Password-456!', role=User.Role.TEACHER)
        profile = user.teacher_profile
        payload = {
            'password': 'Temporary-Password-789!',
            'require_password_change': True,
        }

        denied = self.client.patch(f'/api/v1/roster-teachers/{profile.id}/', payload, format='json')
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        admin_client = APIClient()
        admin_client.force_authenticate(User.objects.create_user(username='boss', role=User.Role.ADMIN))
        response = admin_client.patch(f'/api/v1/roster-teachers/{profile.id}/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertNotIn('password', response.data)
        user.refresh_from_db()
        self.assertTrue(user.check_password(payload['password']))
        self.assertTrue(user.must_change_password)

    def test_non_management_roles_cannot_edit(self):
        profile = User.objects.create_user(username='t1', role=User.Role.TEACHER).teacher_profile
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username='p1', role=User.Role.PARENT))

        response = client.patch(f'/api/v1/roster-teachers/{profile.id}/', {'employee_id': 'E1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_endpoints_do_not_allow_delete_or_create(self):
        profile = User.objects.create_user(username='t1', role=User.Role.TEACHER).teacher_profile
        self.assertEqual(
            self.client.delete(f'/api/v1/roster-teachers/{profile.id}/').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.post('/api/v1/roster-teachers/', {}, format='json').status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )


class RosterParentAndStudentEditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(User.objects.create_user(username='editor', role=User.Role.STAFF))

    def test_parent_without_a_login_can_be_edited_even_when_parents_association_is_off(self):
        config = AcademicConfiguration.load()
        config.parents_association_enabled = False
        config.save()
        guardian = Guardian.objects.create(full_name='Imported Parent')

        response = self.client.patch(
            f'/api/v1/roster-parents/{guardian.id}/', {'full_name': 'Parent Roe', 'phone_1': '012'}, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        guardian.refresh_from_db()
        self.assertEqual((guardian.full_name, guardian.phone_1), ('Parent Roe', '012'))

    def test_parent_name_cannot_be_blank(self):
        guardian = Guardian.objects.create(full_name='Imported Parent')

        response = self.client.patch(f'/api/v1/roster-parents/{guardian.id}/', {'full_name': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_management_roles_cannot_edit_a_parent(self):
        guardian = Guardian.objects.create(full_name='Imported Parent')
        client = APIClient()
        client.force_authenticate(User.objects.create_user(username='p1', role=User.Role.PARENT))

        response = client.patch(f'/api/v1/roster-parents/{guardian.id}/', {'full_name': 'X'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_details_can_be_edited(self):
        student = Student.objects.create(
            student_id='S1', full_name='Kid Roe', sex=Student.Sex.MALE, date_of_birth='2014-01-01',
        )

        response = self.client.patch(
            f'/api/v1/students/{student.id}/',
            {'khmer_name': 'Khmer', 'nationality_1': 'Cambodian', 'sex': 'FEMALE'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        student.refresh_from_db()
        self.assertEqual((student.khmer_name, student.nationality_1, student.sex), ('Khmer', 'Cambodian', 'FEMALE'))
