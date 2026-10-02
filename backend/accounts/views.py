from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .authentication import token_is_expired


class LoginView(ObtainAuthToken):
    # Credentials are supplied in the body, so a stale admin session cookie
    # must not trigger session-based CSRF enforcement on this public endpoint.
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        if not created and token_is_expired(token):
            token.delete()
            token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'username': user.get_username(),
            'role': user.role,
            'must_change_password': user.must_change_password,
        })


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_new_password(self, value):
        user = self.context['request'].user
        if user.check_password(value):
            raise serializers.ValidationError('Choose a password different from your current password.')
        try:
            validate_password(value, user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data['current_password']):
            raise ValidationError({'current_password': 'Current password is incorrect.'})
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])
        return Response(status=204)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if isinstance(request.auth, Token):
            request.auth.delete()
        return Response(status=204)
