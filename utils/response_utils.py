"""
Utility functions for standardized API responses and error handling.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Union
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import HttpRequest, Http404
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response utility class"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        meta: Optional[Dict] = None
    ) -> Response:
        """Return a standardized success response"""
        response_data = {
            "success": True,
            "message": message,
            "data": data
        }

        if meta:
            response_data["meta"] = meta

        return Response(response_data, status=status_code)

    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: Optional[List] = None,
        error_code: Optional[str] = None
    ) -> Response:
        """Return a standardized error response"""
        response_data = {
            "success": False,
            "message": message,
            "error_code": error_code
        }

        if errors:
            response_data["errors"] = errors

        return Response(response_data, status=status_code)

    @staticmethod
    def created(data: Any = None, message: str = "Resource created successfully") -> Response:
        """Return a standardized created response"""
        return APIResponse.success(data, message, status.HTTP_201_CREATED)

    @staticmethod
    def no_content(message: str = "No content") -> Response:
        """Return a standardized no content response"""
        return APIResponse.success(None, message, status.HTTP_204_NO_CONTENT)

    @staticmethod
    def not_found(message: str = "Resource not found") -> Response:
        """Return a standardized not found response"""
        return APIResponse.error(message, status.HTTP_404_NOT_FOUND, error_code="NOT_FOUND")

    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Response:
        """Return a standardized unauthorized response"""
        return APIResponse.error(message, status.HTTP_401_UNAUTHORIZED, error_code="UNAUTHORIZED")

    @staticmethod
    def forbidden(message: str = "Access denied") -> Response:
        """Return a standardized forbidden response"""
        return APIResponse.error(message, status.HTTP_403_FORBIDDEN, error_code="FORBIDDEN")

    @staticmethod
    def server_error(message: str = "Internal server error") -> Response:
        """Return a standardized server error response"""
        return APIResponse.error(message, status.HTTP_500_INTERNAL_SERVER_ERROR, error_code="SERVER_ERROR")

    @staticmethod
    def validation_error(errors: List, message: str = "Validation failed") -> Response:
        """Return a standardized validation error response"""
        return APIResponse.error(message, status.HTTP_400_BAD_REQUEST, errors, "VALIDATION_ERROR")


def handle_exceptions(func):
    """Decorator for consistent exception handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            return APIResponse.validation_error([str(e)])
        except Http404:
            logger.warning(f"Resource not found in {func.__name__}")
            return APIResponse.not_found()
        except PermissionError as e:
            logger.warning(f"Permission error in {func.__name__}: {str(e)}")
            return APIResponse.forbidden(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return APIResponse.server_error()
    return wrapper


def validate_required_fields(data: Dict, required_fields: List[str]) -> List[str]:
    """Validate that required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    return missing_fields


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not isinstance(value, str):
        return str(value)

    # Remove HTML tags
    sanitized = strip_tags(value)

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', sanitized)

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def sanitize_dict(data: Dict, max_length: int = 1000) -> Dict:
    """Sanitize all string values in a dictionary"""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value, max_length)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, max_length)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item, max_length) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def paginate_response(
    queryset,
    page: int = 1,
    page_size: int = 20,
    serializer_class=None,
    request=None
) -> Response:
    """Create a standardized paginated response"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    paginator = Paginator(queryset, page_size)

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    if serializer_class:
        data = serializer_class(items, many=True, context={'request': request}).data
    else:
        data = list(items)

    meta = {
        "pagination": {
            "current_page": items.number,
            "total_pages": paginator.num_pages,
            "total_items": paginator.count,
            "page_size": page_size,
            "has_next": items.has_next(),
            "has_previous": items.has_previous(),
        }
    }

    return APIResponse.success(data, meta=meta)


def log_api_request(request: HttpRequest, response: Response, duration: float = None):
    """Log API request details for monitoring"""
    log_data = {
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "user_id": getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        "ip_address": get_client_ip(request),
    }

    if duration:
        log_data["duration"] = duration

    if response.status_code >= 400:
        logger.warning(f"API Request: {log_data}")
    else:
        logger.info(f"API Request: {log_data}")


def get_client_ip(request: HttpRequest) -> str:
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# Constants for common error messages
ERROR_MESSAGES = {
    "VALIDATION_ERROR": "The provided data is invalid",
    "NOT_FOUND": "The requested resource was not found",
    "UNAUTHORIZED": "Authentication is required to access this resource",
    "FORBIDDEN": "You do not have permission to access this resource",
    "SERVER_ERROR": "An internal server error occurred",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later",
    "FILE_TOO_LARGE": "The uploaded file is too large",
    "INVALID_FILE_TYPE": "The uploaded file type is not allowed",
    "DUPLICATE_ENTRY": "A record with this information already exists",
    "INVALID_CREDENTIALS": "Invalid username or password",
    "ACCOUNT_LOCKED": "Your account has been temporarily locked",
    "EMAIL_NOT_VERIFIED": "Please verify your email address",
    "PASSWORD_TOO_WEAK": "Password does not meet security requirements",
    "TOKEN_EXPIRED": "Your session has expired. Please log in again",
    "INVALID_TOKEN": "The provided token is invalid or expired",
}
