from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError

from core.exceptions import api_exception_handler


class ApiExceptionHandlerTests(SimpleTestCase):
    def test_unexpected_error_returns_json_500(self):
        with self.assertLogs('api', level='ERROR'):
            response = api_exception_handler(RuntimeError('boom'), {'request': None})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {'detail': 'Internal server error.'})

    def test_validation_error_keeps_drf_shape(self):
        response = api_exception_handler(ValidationError({'name': ['Required.']}), {'request': None})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'name': ['Required.']})
