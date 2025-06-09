import logging
import os
import json
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

from .models import CustomUser, UserProfile
from .serializers import UserRegistrationSerializer

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
import secrets
from django.shortcuts import redirect
from django.http import HttpResponseBadRequest
from .google_oauth import GoogleOAuth

@api_view(['GET'])
@permission_classes([AllowAny])
def get_google_client_id(request):
    """Return the Google OAuth client ID for frontend use"""
    return Response({
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def oauth_start(request):
    """
    Start the Google OAuth 2.0 flow by generating a state token and redirecting
    to the Google authorization URL.
    """
    # Generate a secure random string for state
    state = secrets.token_urlsafe(32)
    request.session['oauth_state'] = state
    
    # Get the authorization URL from GoogleOAuth helper
    oauth = GoogleOAuth()
    auth_url = oauth.get_auth_url(state=state)
    
    return Response({
        'auth_url': auth_url
    }, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def oauth_callback(request):
    """
    Handle the callback from Google OAuth 2.0.
    This will exchange the authorization code for tokens and create/login the user.
    """
    # Get the code and state from the request
    code = request.GET.get('code')
    received_state = request.GET.get('state')
    
    # Validate state to prevent CSRF
    expected_state = request.session.get('oauth_state')
    if not received_state or not expected_state or received_state != expected_state:
        return HttpResponseBadRequest("Invalid state parameter. Possible CSRF attack.")
    
    # Clear the state from session
    if 'oauth_state' in request.session:
        del request.session['oauth_state']
    
    if not code:
        return HttpResponseBadRequest("No authorization code provided")
    
    # Exchange the authorization code for tokens
    oauth = GoogleOAuth()
    token_data = oauth.exchange_code_for_token(code)
    
    if not token_data:
        return HttpResponseBadRequest("Failed to exchange authorization code for token")
    
    # Get user info with the access token
    access_token = token_data.get('access_token')
    user_data = oauth.get_user_info(access_token)
    
    if not user_data:
        return HttpResponseBadRequest("Failed to get user information")
    
    try:
        # Extract user information
        email = user_data.get('email')
        
        if not email:
            return HttpResponseBadRequest("Email not provided by Google")
        
        # Check if email is verified by Google
        if not user_data.get('email_verified', False):
            return HttpResponseBadRequest("Email not verified by Google")
            
        # Check if user exists, if not create one
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'is_email_verified': True  # Email is verified by Google
            }
        )
          # If user was just created, set up their profile
        if created:
            # Set default role as applicant
            user.set_as_applicant()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                name=f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}".strip(),
                email=email,
                profile_picture=user_data.get('picture', '')
            )
        
        # Generate authentication tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare user data
        user_info = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.get_role(),
            'is_new_user': created,
            'google_data': {
                'name': f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}".strip(),
                'picture': user_data.get('picture', '')
            }
        }
        
        # Create the response data
        auth_data = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_info
        }
        
        # Redirect to the frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/auth/google/callback"
        redirect_params = {
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user_data': json.dumps(user_info)
        }
        
        # Return a redirect response to the frontend with the tokens
        return redirect(f"{redirect_url}?{urlencode(redirect_params)}")
        
    except Exception as e:
        # Any errors
        logging.error(f"OAuth error: {e}")
        return HttpResponseBadRequest(f"Authentication failed: {str(e)}")

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def exchange_code(request):
    """
    API endpoint that exchanges a Google OAuth code for tokens.
    Used as an alternative for the redirected OAuth flow.
    """
    code = request.data.get('code')
    if not code:
        return Response({"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Exchange the authorization code for tokens
        oauth = GoogleOAuth()
        token_data = oauth.exchange_code_for_token(code)
        
        if not token_data:
            return Response({"error": "Failed to exchange code for token"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user info with the access token
        access_token = token_data.get('access_token')
        user_data = oauth.get_user_info(access_token)
        
        if not user_data:
            return Response({"error": "Failed to get user information"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract user information
        email = user_data.get('email')
        
        if not email:
            return Response({"error": "Email not provided by Google"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email is verified by Google
        if not user_data.get('email_verified', False):
            return Response({"error": "Email not verified by Google"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if user exists, if not create one
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
                'is_email_verified': True  # Email is verified by Google
            }
        )
        
        # If user was just created, set up their profile
        if created:
            # Set default role as applicant
            user.set_as_applicant()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                name=f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}".strip(),
                email=email,
                profile_picture=user_data.get('picture', '')
            )
        
        # Generate authentication tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare user data for response
        user_info = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.get_role(),
            'is_new_user': created,
            'google_data': {
                'name': f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}".strip(),
                'picture': user_data.get('picture', '')
            }
        }
        
        # Return tokens and user info
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': user_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Any errors
        logging.error(f"Token exchange error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
