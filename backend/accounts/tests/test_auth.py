from datetime import timedelta

from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User

LOGIN_URL = '/api/v1/auth-token/'
CREDENTIALS = {'username': 'staffer', 'password': 'Str0ngPass!23'}


class AuthTokenTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)

    def test_valid_credentials_return_token(self):
        response = self.client.post(LOGIN_URL, CREDENTIALS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())
        self.assertEqual((response.json()['username'], response.json()['role']), ('staffer', 'STAFF'))
        self.assertFalse(response.json()['must_change_password'])

    def test_must_change_password_blocks_role_apis_until_password_is_changed(self):
        self.user.must_change_password = True
        self.user.save(update_fields=['must_change_password'])

        login = self.client.post(LOGIN_URL, CREDENTIALS)
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertTrue(login.json()['must_change_password'])
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {login.json()['token']}")

        blocked = client.get('/api/v1/students/')
        changed = client.post('/api/v1/auth/change-password/', {
            'current_password': CREDENTIALS['password'],
            'new_password': 'A-New-Strong-Pass!456',
        }, format='json')
        allowed = client.get('/api/v1/students/')

        self.assertEqual(blocked.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(changed.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(self.user.check_password('A-New-Strong-Pass!456'))

    def test_change_password_requires_the_current_password(self):
        token = Token.objects.create(user=self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.post('/api/v1/auth/change-password/', {
            'current_password': 'wrong',
            'new_password': 'A-New-Strong-Pass!456',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password(CREDENTIALS['password']))

    def test_invalid_credentials_rejected(self):
        response = self.client.post(LOGIN_URL, {'username': 'staffer', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_ignores_stale_authenticated_session(self):
        # Regression test: a pre-existing Django session (e.g. from /admin/) must not
        # trigger CSRF enforcement on this public, credential-based endpoint.
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(LOGIN_URL, CREDENTIALS)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_post_ignores_stale_session_csrf(self):
        # Regression: roster "Add User" failed with "CSRF token missing" after an /admin/ login.
        token = Token.objects.create(user=self.user)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(
            '/api/v1/roster-users/',
            {'user_type': User.Role.TEACHER, 'first_name': 'T', 'last_name': 'T', 'email': 't@example.com', 'send_welcome_email': False},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Token {token.key}',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

    def test_login_is_rate_limited(self):
        statuses = [self.client.post(LOGIN_URL, {'username': 'staffer', 'password': 'wrong'}).status_code
                    for _ in range(6)]
        self.assertEqual(statuses[:5], [status.HTTP_400_BAD_REQUEST] * 5)
        self.assertEqual(statuses[5], status.HTTP_429_TOO_MANY_REQUESTS)


class TokenLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='staffer', password='Str0ngPass!23', role=User.Role.STAFF)

    def _expire(self, token):
        Token.objects.filter(pk=token.pk).update(created=timezone.now() - timedelta(hours=13))

    def test_expired_token_is_rejected_and_removed(self):
        token = Token.objects.create(user=self.user)
        self._expire(token)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.get('/api/v1/students/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())

    def test_login_replaces_an_expired_token(self):
        old = Token.objects.create(user=self.user)
        self._expire(old)

        response = self.client.post(LOGIN_URL, CREDENTIALS)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.json()['token'], old.key)

    def test_login_reuses_a_valid_token(self):
        token = Token.objects.create(user=self.user)
        response = self.client.post(LOGIN_URL, CREDENTIALS)
        self.assertEqual(response.json()['token'], token.key)

    def test_logout_deletes_the_token(self):
        token = Token.objects.create(user=self.user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = client.post('/api/v1/auth/logout/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())

    def test_logout_requires_authentication(self):
        response = APIClient().post('/api/v1/auth/logout/')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
