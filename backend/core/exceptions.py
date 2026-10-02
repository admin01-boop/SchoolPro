import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger('api')


def api_exception_handler(exc, context):
    """DRF's default error shape, plus logging and a JSON body for unexpected errors."""
    response = exception_handler(exc, context)
    request = context.get('request')
    route = f'{request.method} {request.path}' if request else 'unknown request'

    if response is None:
        logger.exception('Unhandled error on %s', route)
        return Response({'detail': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if response.status_code >= 500:
        logger.error('Server error %s on %s', response.status_code, route, exc_info=exc)
    else:
        logger.info('%s on %s: %s', response.status_code, route, response.data)
    return response
