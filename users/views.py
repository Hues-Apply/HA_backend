import logging
import os
import json
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import ProfilePermissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import CustomUser, UserProfile
from .serializers import UserRegistrationSerializer, CustomUserSerializer
from utils.response_utils import APIResponse, sanitize_dict, handle_exceptions

# Configure logging
logger = logging.getLogger(__name__)

# Import our simple Google OAuth functions
try:
    logger.info("Attempting to import Google OAuth functions...")
    from .google_oauth import exchange_code_for_tokens, get_user_info_from_id_token, refresh_access_token
    GOOGLE_OAUTH_AVAILABLE = True
    logger.info("Google OAuth functions imported successfully")
except ImportError as e:
    logger.error(f"Google OAuth modules not available: {e}. OAuth functionality will be disabled.")
    GOOGLE_OAUTH_AVAILABLE = False
    # Define stub functions to prevent runtime errors
    def exchange_code_for_tokens(code):
        raise ValidationError("Google OAuth not available")
    def get_user_info_from_id_token(token):
        raise ValidationError("Google OAuth not available")
    def refresh_access_token(token):
        raise ValidationError("Google OAuth not available")
except Exception as e:
    logger.error(f"Unexpected error importing Google OAuth: {e}")
    GOOGLE_OAUTH_AVAILABLE = False
    # Define stub functions to prevent runtime errors
    def exchange_code_for_tokens(code):
        raise ValidationError("Google OAuth not available")
    def get_user_info_from_id_token(token):
        raise ValidationError("Google OAuth not available")
    def refresh_access_token(token):
        raise ValidationError("Google OAuth not available")

User = get_user_model()

# REST API views for role management
class UserRoleAPIView(APIView):
    permission_classes = [ProfilePermissions]

    def get(self, request):
        """Get current user role"""
        return APIResponse.success({
            'role': request.user.get_role(),
            'is_applicant': request.user.is_applicant(),
            'is_employer': request.user.is_employer(),
            'is_admin': request.user.is_superuser
        })

    def post(self, request):
        """Update user role"""
        # Sanitize input
        sanitized_data = sanitize_dict(request.data)
        role = sanitized_data.get('role')

        if role == 'applicant':
            request.user.set_as_applicant()
            return APIResponse.success(message='Role updated to Applicant')
        elif role == 'employer':
            request.user.set_as_employer()
            return APIResponse.success(message='Role updated to Employer')
        else:
            return APIResponse.error('Invalid role specified', status.HTTP_400_BAD_REQUEST)


class GoogleAuthMixin:
    """Mixin to handle Google OAuth authentication logic"""

    def _authenticate_google_user(self, user_data, require_email_verification=True):
        """Shared method to authenticate or create Google user"""
        try:
            user_email = user_data.get('email')
            if not user_email:
                raise ValidationError("Email is required for authentication")
            
            # Verify email is verified if required
            if require_email_verification and not user_data.get('email_verified', False):
                logger.warning(f"Email not verified by Google for user: {user_email}")
                raise ValidationError("Email not verified by Google")

            # Create or get user with transaction safety
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=user_email,
                    defaults={
                        'first_name': user_data.get('given_name', ''),
                        'last_name': user_data.get('family_name', ''),
                        'is_email_verified': True,
                        'is_active': True
                    }
                )

                if created:
                    logger.info(f"Created new user: {user.email}")
                    # Set default role for new users
                    user.set_as_applicant()
                else:
                    logger.info(f"Existing user logged in: {user.email}")

                # Create or get user profile
                profile, _ = UserProfile.objects.get_or_create(user=user)
                
                # Update profile with Google data
                if user_data.get('picture'):
                    profile.google_picture = user_data['picture']
                if user_data.get('sub'):
                    profile.google_id = user_data['sub']
                profile.save()

            # Generate JWT tokens
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                logger.info(f"Generated JWT tokens for user: {user.email}")

                return {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.get_role(),
                        'is_applicant': user.is_applicant(),
                        'is_employer': user.is_employer(),
                        'is_admin': user.is_superuser,
                        'is_new_user': created  # Add this field for frontend routing
                    }
                }

            except Exception as jwt_error:
                logger.error(f"JWT generation failed: {jwt_error}")
                raise ValidationError("Authentication token generation failed")

        except Exception as e:
            logger.error(f"User authentication error: {str(e)}", exc_info=True)
            raise


# Google Sign-in views
class GoogleAuthCallbackView(GoogleAuthMixin, APIView):
    """
    Google OAuth callback - exchanges authorization code for tokens
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Sanitize input
        sanitized_data = sanitize_dict(request.data)
        code = sanitized_data.get('code')
        logger.debug(f"Received OAuth code: {code[:10] if code else 'None'}...")

        if not code:
            logger.warning("No authorization code provided in request")
            return APIResponse.error("Authorization code is required", status.HTTP_400_BAD_REQUEST)

        try:
            # Check if Google OAuth is available
            if not settings.GOOGLE_OAUTH_ENABLED:
                logger.error("Google OAuth not enabled")
                return APIResponse.error("Google OAuth service unavailable", status.HTTP_503_SERVICE_UNAVAILABLE)

            logger.debug(f"Processing OAuth code of length: {len(code) if code else 0}")
            
            # Exchange code for tokens
            tokens = exchange_code_for_tokens(code)
            if not tokens:
                logger.error("Failed to exchange code for tokens")
                return APIResponse.error("Failed to authenticate with Google", status.HTTP_401_UNAUTHORIZED)

            logger.debug(f"Received tokens with keys: {list(tokens.keys()) if tokens else 'None'}")

            # Get user info from ID token
            user_data = get_user_info_from_id_token(tokens['id_token'])
            if not user_data:
                logger.error("Failed to get user info from ID token")
                return APIResponse.error("Failed to get user information", status.HTTP_401_UNAUTHORIZED)

            logger.debug(f"Retrieved user data for email: {user_data.get('email', 'unknown')}")

            # Authenticate user using shared method
            result = self._authenticate_google_user(user_data, require_email_verification=False)
            return APIResponse.success(result)

        except ValidationError as e:
            return APIResponse.error(str(e), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
            return APIResponse.error("Authentication failed", status.HTTP_401_UNAUTHORIZED)


class GoogleCredentialAuthView(GoogleAuthMixin, APIView):
    """
    Google Sign-in with credential token (ID token)
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Sanitize input
        sanitized_data = sanitize_dict(request.data)
        credential = sanitized_data.get('credential')
        logger.debug(f"Received Google credential token: {credential[:50] if credential else 'None'}...")

        if not credential:
            logger.warning("No credential provided in request")
            return APIResponse.error("Google credential token is required", status.HTTP_400_BAD_REQUEST)

        try:
            # Check if Google OAuth is available
            if not settings.GOOGLE_OAUTH_ENABLED:
                logger.error("Google OAuth not enabled")
                return APIResponse.error("Google OAuth not available", status.HTTP_503_SERVICE_UNAVAILABLE)

            # Extract user info directly from ID token (credential)
            user_data = get_user_info_from_id_token(credential)
            if not user_data:
                logger.error("Failed to get user info from ID token")
                return APIResponse.error("Failed to get user information", status.HTTP_401_UNAUTHORIZED)

            # Authenticate user using shared method
            result = self._authenticate_google_user(user_data, require_email_verification=True)
            return APIResponse.success(result)

        except ValidationError as e:
            return APIResponse.error(str(e), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Google credential authentication error: {str(e)}", exc_info=True)
            return APIResponse.error("Authentication failed", status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_refresh_token(request):
    """Refresh Google access token"""
    # Sanitize input
    sanitized_data = sanitize_dict(request.data)
    refresh_token = sanitized_data.get('refreshToken')

    if not refresh_token:
        return APIResponse.error("Refresh token is required", status.HTTP_400_BAD_REQUEST)

    try:
        if not GOOGLE_OAUTH_AVAILABLE:
            return APIResponse.error("Google OAuth not available", status.HTTP_503_SERVICE_UNAVAILABLE)

        # Refresh the access token
        credentials = refresh_access_token(refresh_token)
        return APIResponse.success(credentials)

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return APIResponse.error(str(e), status.HTTP_400_BAD_REQUEST)


class GoogleClientIDView(APIView):
    """API View to provide Google Client ID to frontend"""
    permission_classes = [AllowAny]

    def get(self, request):
        return APIResponse.success({
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def get_google_client_id(request):
    """Return the Google OAuth client ID for frontend use (legacy endpoint)"""
    return APIResponse.success({
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
    })


@api_view(['POST'])
@permission_classes([ProfilePermissions])
def sign_out(request):
    """Blacklist the user's refresh token"""
    try:
        # Sanitize input
        sanitized_data = sanitize_dict(request.data)
        refresh_token = sanitized_data.get('refresh_token')

        if not refresh_token:
            return APIResponse.error("Refresh token is required", status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return APIResponse.success(message="User logged out successfully")
    except Exception as e:
        return APIResponse.error(str(e), status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """API endpoint for user registration with role selection"""
    # Sanitize input
    sanitized_data = sanitize_dict(request.data)
    serializer = UserRegistrationSerializer(data=sanitized_data)

    if serializer.is_valid():
        try:
            user = serializer.save()

            # Generate authentication tokens
            refresh = RefreshToken.for_user(user)

            # Prepare user data
            user_info = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.get_role(),
                'is_new_user': True
            }

            # Return tokens and user info
            return APIResponse.created({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': user_info
            })
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            return APIResponse.error("Registration failed", status.HTTP_500_INTERNAL_SERVER_ERROR)

    return APIResponse.validation_error(serializer.errors)
