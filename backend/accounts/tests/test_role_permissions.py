from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsParent, IsStudent, IsTeacher, role_required


def _call(permission, user):
    class View(APIView):
        permission_classes = [permission]

        def get(self, request):
            return Response({'ok': True})

    request = APIRequestFactory().get('/stub/')
    if user is not None:
        force_authenticate(request, user=user)
    return View.as_view()(request)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='t1', password='Str0ngPass!23', role=User.Role.TEACHER)
        self.parent = User.objects.create_user(username='p1', password='Str0ngPass!23', role=User.Role.PARENT)
        self.student = User.objects.create_user(username='s1', password='Str0ngPass!23', role=User.Role.STUDENT)

    def test_each_role_class_allows_only_its_role(self):
        cases = [(IsTeacher, self.teacher), (IsParent, self.parent), (IsStudent, self.student)]
        for permission, allowed_user in cases:
            for user in (self.teacher, self.parent, self.student):
                expected = status.HTTP_200_OK if user == allowed_user else status.HTTP_403_FORBIDDEN
                self.assertEqual(_call(permission, user).status_code, expected, (permission.__name__, user.role))

    def test_role_required_accepts_several_roles(self):
        permission = role_required(User.Role.TEACHER, User.Role.PARENT)
        self.assertEqual(_call(permission, self.teacher).status_code, status.HTTP_200_OK)
        self.assertEqual(_call(permission, self.parent).status_code, status.HTTP_200_OK)
        self.assertEqual(_call(permission, self.student).status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_denied(self):
        response = _call(IsTeacher, None)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
