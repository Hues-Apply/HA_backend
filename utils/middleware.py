"""
Custom middleware to handle read-only transaction errors gracefully.
"""
import logging
from django.http import JsonResponse
from django.db.utils import DatabaseError
from psycopg2.errors import ReadOnlySqlTransaction

logger = logging.getLogger(__name__)


class ReadOnlyTransactionMiddleware:
    """
    Middleware to handle read-only transaction errors gracefully.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except ReadOnlySqlTransaction as e:
            logger.error(f"Read-only transaction error in {request.path}: {e}")

            # For admin login, return a specific error message
            if request.path.startswith('/admin/login'):
                return JsonResponse({
                    'error': 'Database is currently in read-only mode. Please try again later.',
                    'details': 'The database is temporarily unavailable for write operations.'
                }, status=503)

            # For API endpoints, return a JSON error
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Service temporarily unavailable',
                    'message': 'The database is currently in read-only mode. Please try again later.'
                }, status=503)

            # For other requests, return a generic error
            return JsonResponse({
                'error': 'Service temporarily unavailable'
            }, status=503)

        except DatabaseError as e:
            logger.error(f"Database error in {request.path}: {e}")
            return JsonResponse({
                'error': 'Database error occurred',
                'message': 'Please try again later.'
            }, status=500)
