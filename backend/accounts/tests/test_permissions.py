from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsStaffRole


class _StaffOnlyView(APIView):
    permission_classes = [IsStaffRole]

    def get(self, request):
        return Response({'ok': True})


class IsStaffRolePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = _StaffOnlyView.as_view()

    def _call(self, user=None):
        request = self.factory.get('/stub/')
        if user is not None:
            force_authenticate(request, user=user)
        return self.view(request)

    def test_staff_role_allowed(self):
        user = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)
        response = self._call(user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_parent_role_forbidden(self):
        user = User.objects.create_user(username='parent1', password='Str0ngPass!23', role=User.Role.PARENT)
        response = self._call(user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_observer_role_forbidden(self):
        user = User.objects.create_user(username='observer1', password='Str0ngPass!23', role=User.Role.OBSERVER)
        response = self._call(user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_allowed_regardless_of_role(self):
        user = User.objects.create_superuser(username='root', password='Str0ngPass!23', email='root@example.com')
        response = self._call(user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        response = self._call(None)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

