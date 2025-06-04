import os
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
@api_view(['GET'])
@permission_classes([AllowAny])
def get_google_client_id(request):
    """Return the Google OAuth client ID for frontend use"""
    return Response({
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
    }, status=status.HTTP_200_OK)

from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def auth_receiver(request):
    """
    API endpoint that receives a Google credential token from the frontend 
    and authenticates the user.
    """
    # Get token from request data
    credential = request.data.get('credential')
    if not credential:
        return Response({"error": "No credential provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify the token with Google
        user_data = id_token.verify_oauth2_token(
            credential, 
            requests.Request(), 
            settings.GOOGLE_OAUTH_CLIENT_ID
        )
        
        # Get user info from the verified token
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
        
    except ValueError as e:
        # Invalid token
        print(f"Token validation error: {e}")
        return Response({"error": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)

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
