import logging
import os
import json
from urllib.parse import urlencode
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

# Configure logging
logger = logging.getLogger(__name__)

# Import our simple Google OAuth functions
try:
    logger.info("Attempting to import Google OAuth functions...")
    from .google_oauth import exchange_code_for_tokens, get_user_info_from_id_token, refresh_access_token
    GOOGLE_OAUTH_AVAILABLE = True
    logger.info("Google OAuth functions imported successfully")
except ImportError as e:
    logger.warning(f"Google OAuth modules not available: {e}. OAuth functionality will be disabled.")
    GOOGLE_OAUTH_AVAILABLE = False
except Exception as e:
    logger.error(f"Unexpected error importing Google OAuth: {e}")
    GOOGLE_OAUTH_AVAILABLE = False

User = get_user_model()

# REST API views for role management
class UserRoleAPIView(APIView):
    permission_classes = [ProfilePermissions]

    def get(self, request):
        """Get current user role"""
        return Response({
            'role': request.user.get_role(),
            'is_applicant': request.user.is_applicant(),
            'is_employer': request.user.is_employer(),
            'is_admin': request.user.is_superuser
        })

    def post(self, request):
        """Update user role"""
        role = request.data.get('role')

        if role == 'applicant':
            request.user.set_as_applicant()
            return Response({'message': 'Role updated to Applicant'})
        elif role == 'employer':
            request.user.set_as_employer()
            return Response({'message': 'Role updated to Employer'})
        else:
            return Response(
                {'error': 'Invalid role specified'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Google Sign-in views

class GoogleAuthCallbackView(APIView):
    """
    Simple Google OAuth callback - equivalent to app.post('/auth/google', ...)
    Exchanges Google OAuth code for tokens and user info
    """
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        logger.debug(f"Received OAuth code: {code[:10]}...")

        if not code:
            logger.warning("No authorization code provided in request")
            return Response(
                {"error": "Authorization code is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            logger.debug(f"GOOGLE_OAUTH_AVAILABLE: {GOOGLE_OAUTH_AVAILABLE}")

            # Check if Google OAuth is available
            if not GOOGLE_OAUTH_AVAILABLE:
                logger.error("Google OAuth not available")
                return Response(
                    {"error": "Google OAuth service unavailable"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Exchange code for tokens
            tokens = exchange_code_for_tokens(code)
            if not tokens:
                logger.error("Failed to exchange code for tokens")
                return Response(
                    {"error": "Failed to authenticate with Google"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Get user info from ID token
            user_data = get_user_info_from_id_token(tokens['id_token'])
            if not user_data:
                logger.error("Failed to get user info from ID token")
                return Response(
                    {"error": "Failed to get user information"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Create or get user
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'first_name': user_data.get('given_name', ''),
                        'last_name': user_data.get('family_name', ''),
                        'is_active': True
                    }
                )

                if created:
                    logger.info(f"Created new user: {user.email}")
                else:
                    logger.info(f"Existing user logged in: {user.email}")

                # Create or get user profile
                profile, _ = UserProfile.objects.get_or_create(user=user)

            # Generate JWT tokens
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                logger.info(f"Generated JWT tokens for user: {user.email}")

                return Response({
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
                        'is_admin': user.is_superuser
                    }
                })

            except Exception as jwt_error:
                logger.error(f"JWT generation failed: {jwt_error}")
                return Response(
                    {"error": "Authentication token generation failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
            return Response(
                {"error": "Authentication failed"},
                status=status.HTTP_401_UNAUTHORIZED
            )

@api_view(['POST'])
@permission_classes([AllowAny])
def google_refresh_token(request):
    """
    Refresh Google access token - equivalent to app.post('/auth/google/refresh-token', ...)
    """
    refresh_token = request.data.get('refreshToken')

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if not GOOGLE_OAUTH_AVAILABLE:
            return Response(
                {"error": "Google OAuth not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Refresh the access token
        credentials = refresh_access_token(refresh_token)

        return Response(credentials, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

class GoogleClientIDView(APIView):
    """
    API View to provide Google Client ID to frontend
    """
    permission_classes = [AllowAny]  # Public endpoint

    def get(self, request):
        return Response({
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_google_client_id(request):
    """Return the Google OAuth client ID for frontend use (legacy endpoint)"""
    return Response({
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([ProfilePermissions])
def sign_out(request):
    """Blacklist the user's refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"success": "User logged out successfully"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """API endpoint for user registration with role selection"""
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
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
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_info
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GoogleCredentialAuthView(APIView):
    """
    Google Sign-in with credential token (ID token)
    Handles POST /api/auth/google/ endpoint
    """
    permission_classes = [AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        logger.debug(f"Received Google credential token: {credential[:50] if credential else 'None'}...")

        if not credential:
            logger.warning("No credential provided in request")
            return Response(
                {"error": "Google credential token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if Google OAuth is available
            if not GOOGLE_OAUTH_AVAILABLE:
                logger.error("Google OAuth not available")
                return Response(
                    {"error": "Google OAuth not available"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Extract user info directly from ID token (credential)
            user_data = get_user_info_from_id_token(credential)
            if not user_data:
                logger.error("Failed to get user info from ID token")
                return Response(
                    {"error": "Failed to get user information"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Verify email is verified
            if not user_data.get('email_verified', False):
                logger.warning(f"Email not verified by Google for user: {user_data.get('email', 'unknown')}")
                return Response(
                    {"error": "Email not verified by Google"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get or create user
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'first_name': user_data.get('given_name', ''),
                        'last_name': user_data.get('family_name', ''),
                        'is_email_verified': True,
                    }
                )
                if created:
                    logger.info(f"Created new user: {user.email}")
                else:
                    logger.info(f"Existing user logged in: {user.email}")

                # Create or get user profile
                profile, _ = UserProfile.objects.get_or_create(user=user)

            # Generate JWT tokens
            try:
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                logger.info(f"Generated JWT tokens for user: {user.email}")

                return Response({
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
                        'is_admin': user.is_superuser
                    }
                })

            except Exception as jwt_error:
                logger.error(f"JWT generation failed: {jwt_error}")
                return Response(
                    {"error": "Authentication token generation failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Google credential authentication error: {str(e)}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
