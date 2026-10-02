from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


def token_is_expired(token):
    lifetime = timedelta(hours=settings.AUTH_TOKEN_TTL_HOURS)
    return timezone.now() - token.created > lifetime


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if token_is_expired(token):
            token.delete()
            raise AuthenticationFailed('Token has expired. Please sign in again.')
        return user, token
