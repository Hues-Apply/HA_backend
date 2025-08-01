"""
Utility functions for standardized API responses and error handling.
"""
import logging
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404
from config.constants import ERROR_MESSAGES, SUCCESS_MESSAGES, API_RESPONSE_FORMAT

logger = logging.getLogger(__name__)

class APIResponse:
    """Standardized API response wrapper."""

    @staticmethod
    def success(data=None, message="", status_code=status.HTTP_200_OK):
        """Return a successful API response."""
        response_data = {
            'success': True,
            'data': data,
            'message': message,
            'errors': []
        }
        return Response(response_data, status=status_code)

    @staticmethod
    def error(message="", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Return an error API response."""
        response_data = {
            'success': False,
            'data': None,
            'message': message,
            'errors': errors or []
        }
        return Response(response_data, status=status_code)

    @staticmethod
    def created(data=None, message=""):
        """Return a 201 Created response."""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)

    @staticmethod
    def no_content(message=""):
        """Return a 204 No Content response."""
        return APIResponse.success(None, message, status.HTTP_204_NO_CONTENT)

    @staticmethod
    def not_found(message=""):
        """Return a 404 Not Found response."""
        return APIResponse.error(
            message or ERROR_MESSAGES['resource_not_found'],
            status_code=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def unauthorized(message=""):
        """Return a 401 Unauthorized response."""
        return APIResponse.error(
            message or ERROR_MESSAGES['invalid_credentials'],
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def forbidden(message=""):
        """Return a 403 Forbidden response."""
        return APIResponse.error(
            message or ERROR_MESSAGES['permission_denied'],
            status_code=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def server_error(message=""):
        """Return a 500 Internal Server Error response."""
        return APIResponse.error(
            message or ERROR_MESSAGES['server_error'],
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def handle_exceptions(func):
    """Decorator to handle common exceptions and return standardized responses."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            return APIResponse.error(
                ERROR_MESSAGES['validation_error'],
                errors=[str(error) for error in e.messages] if hasattr(e, 'messages') else [str(e)],
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Http404:
            logger.warning(f"Resource not found in {func.__name__}")
            return APIResponse.not_found()
        except PermissionError:
            logger.warning(f"Permission denied in {func.__name__}")
            return APIResponse.forbidden()
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return APIResponse.server_error()
    return wrapper

def validate_required_fields(data, required_fields):
    """Validate that required fields are present in the data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return True

def sanitize_input(text, max_length=1000):
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return text

    # Remove potentially dangerous characters
    import re
    sanitized = re.sub(r'[<>"\']', '', str(text))

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()

def paginate_response(queryset, page, page_size=20, max_page_size=100):
    """Paginate a queryset and return standardized response."""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    # Validate page size
    if page_size > max_page_size:
        page_size = max_page_size

    paginator = Paginator(queryset, page_size)

    try:
        paginated_queryset = paginator.page(page)
    except PageNotAnInteger:
        paginated_queryset = paginator.page(1)
    except EmptyPage:
        paginated_queryset = paginator.page(paginator.num_pages)

    return {
        'results': paginated_queryset.object_list,
        'pagination': {
            'count': paginator.count,
            'next': paginated_queryset.has_next(),
            'previous': paginated_queryset.has_previous(),
            'current_page': paginated_queryset.number,
            'total_pages': paginator.num_pages,
            'page_size': page_size,
        }
    }

def log_api_request(request, response, user=None):
    """Log API request and response for monitoring."""
    log_data = {
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'user_id': user.id if user else None,
        'user_email': user.email if user else None,
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }

    if response.status_code >= 400:
        logger.warning(f"API Error: {log_data}")
    else:
        logger.info(f"API Request: {log_data}")

def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
