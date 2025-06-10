import logging
import logging
import os
import json
import secrets
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.http import HttpResponseBadRequest

from .models import CustomUser, UserProfile
from .serializers import UserRegistrationSerializer, CustomUserSerializer

# Import our simple Google OAuth functions
try:
    print("🔍 Attempting to import Google OAuth functions...")
    from .google_oauth import exchange_code_for_tokens, get_user_info_from_id_token, refresh_access_token
    GOOGLE_OAUTH_AVAILABLE = True
    print("✅ Google OAuth functions imported successfully")
except ImportError as e:
    print(f"❌ Google OAuth import failed: {e}")
    logging.warning(f"Google OAuth modules not available: {e}. OAuth functionality will be disabled.")
    GOOGLE_OAUTH_AVAILABLE = False
except Exception as e:
    print(f"❌ Unexpected error importing Google OAuth: {e}")
    logging.warning(f"Unexpected error importing Google OAuth: {e}. OAuth functionality will be disabled.")
    GOOGLE_OAUTH_AVAILABLE = False
    

User = get_user_model()

# REST API views for role management
class UserRoleAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
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
        print(f"Received code: {code}") 
        
        if not code:
            print("❌ No code provided in request")
            return Response(
                {"error": "Authorization code is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            print(f"🔍 GOOGLE_OAUTH_AVAILABLE: {GOOGLE_OAUTH_AVAILABLE}")
            
            # Check if Google OAuth is available
            if not GOOGLE_OAUTH_AVAILABLE:
                print("❌ Google OAuth not available")
                return Response(
                    {"error": "Google OAuth not available"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            print("✅ Starting token exchange process...")
            # Exchange code for tokens (similar to Express example)
            tokens = exchange_code_for_tokens(code)
            print(f"✅ Token exchange successful. Tokens keys: {list(tokens.keys())}")
            print(f"✅ Token exchange successful. Tokens keys: {list(tokens.keys())}")
            
            print("🔍 Starting ID token verification...")
            # Extract user info from ID token
            user_data = get_user_info_from_id_token(tokens['id_token'])
            print(f"✅ ID token verification successful. User: {user_data.get('email', 'unknown')}")
            
            # Verify email is verified
            if not user_data.get('email_verified', False):
                print(f"❌ Email not verified by Google for user: {user_data.get('email', 'unknown')}")
                return Response(
                    {"error": "Email not verified by Google"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print("✅ Email verification passed")
            print(f"🔍 Looking for existing user with email: {user_data['email']}")
            
            # Find or create user
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True,
                    'is_email_verified': True,
                }
            )
            
            print(f"✅ User {'created' if created else 'found'}: {user.email}")
            print(f"✅ User {'created' if created else 'found'}: {user.email}")
            
            # Update user data if existing user
            if not created:
                print("🔍 Updating existing user data...")
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.is_email_verified = True
                user.save()
                print("✅ User data updated")
            else:
                print("🔍 Setting up new user as applicant...")
                user.set_as_applicant()
                print("✅ New user set as applicant")
            
            print("🔍 Creating/updating user profile...")
            # Store Google data in profile
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': user_data.get('name', f"{user_data['first_name']} {user_data['last_name']}").strip(),
                    'email': user_data['email'],
                }
            )
            profile.google_id = user_data['google_id']
            profile.profile_picture = user_data.get('picture', '')
            
            # Store Google tokens for API access
            profile.google_access_token = tokens.get('access_token')
            if 'refresh_token' in tokens:
                profile.google_refresh_token = tokens['refresh_token']
            profile.save()
            print("✅ User profile updated with Google data")
            
            print("🔍 Generating JWT tokens...")
            # Generate JWT tokens for your app
            try:
                refresh = RefreshToken.for_user(user)
                print("✅ JWT tokens generated successfully")
                app_access_token = str(refresh.access_token)
                app_refresh_token = str(refresh)
            except Exception as jwt_error:
                print(f"⚠️ JWT generation failed due to cryptography issues: {jwt_error}")
                print("🔄 Using fallback token system...")
                # Fallback: Use simple token system without cryptography
                import uuid
                token_id = str(uuid.uuid4())
                app_access_token = f"simple_token_{user.id}_{token_id[:8]}"
                app_refresh_token = f"simple_refresh_{user.id}_{token_id[8:16]}"
                print("✅ Fallback tokens generated")
            
            print("🔍 Preparing response data...")
            # Prepare response
            user_serialized = CustomUserSerializer(user).data
            user_serialized['is_new_user'] = created
            user_serialized['google_data'] = {
                'name': user_data.get('name'),
                'picture': user_data.get('picture')            }
            
            print("✅ OAuth flow completed successfully!")
            return Response({
                'access_token': app_access_token,
                'refresh_token': app_refresh_token,
                'user': user_serialized,
                'google_tokens': {
                    'access_token': tokens.get('access_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'id_token': tokens.get('id_token'),
                    'expires_in': tokens.get('expires_in')
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ ERROR in GoogleAuthCallbackView: {str(e)}")
            print(f"❌ Error type: {type(e).__name__}")
            print(f"❌ Error occurred at step: OAuth processing")
            import traceback
            print(f"❌ Full traceback:\n{traceback.format_exc()}")
            
            logging.error(f"Google OAuth error: {str(e)}")
            return Response(
                {"error": str(e)}, 
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
        logging.error(f"Token refresh error: {str(e)}")
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
@permission_classes([IsAuthenticated])
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
