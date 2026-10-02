from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from academics.models import AcademicConfiguration
from accounts.models import User


class ParentAssociationSettingTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='parent-feature-staff', password='Str0ngPass!23', role=User.Role.STAFF)
        self.client = APIClient()
        self.client.force_authenticate(staff)
        configuration = AcademicConfiguration.load()
        configuration.parents_association_enabled = False
        configuration.save(update_fields=['parents_association_enabled'])

    def test_disabled_parent_association_blocks_its_api_routes(self):
        self.assertEqual(self.client.get('/api/v1/guardians/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/v1/student-guardians/').status_code, status.HTTP_403_FORBIDDEN)

    def test_enabled_parent_association_allows_read_access(self):
        configuration = AcademicConfiguration.load()
        configuration.parents_association_enabled = True
        configuration.save(update_fields=['parents_association_enabled'])
        self.assertEqual(self.client.get('/api/v1/guardians/').status_code, status.HTTP_200_OK)

