"""
Tests for authentication API endpoints
"""
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, BlacklistedToken

from users.models import CustomUser
from tests.test_utils import BaseAPITestCase


class AuthenticationAPITests(BaseAPITestCase):
    """Test authentication API endpoints"""
    
    def test_get_google_client_id(self):
        """Test retrieving Google OAuth client ID"""
        url = reverse('get-google-client-id')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('client_id', response.data)
    
    @override_settings(GOOGLE_OAUTH_CLIENT_ID="test_client_id")
    def test_google_auth_invalid_token(self):
        """Test Google auth with invalid token"""
        url = reverse('google-auth')
        data = {'credential': 'invalid_token'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('register-user')
        data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'applicant'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        
        # Verify that the user was created
        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_applicant())
    
    def test_user_registration_invalid_data(self):
        """Test user registration with invalid data"""
        url = reverse('register-user')
        data = {
            'email': 'invalid-email',
            'password': 'short',
            'role': 'invalid-role'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_sign_out(self):
        """Test sign out endpoint"""
        # First authenticate
        tokens = self.authenticate_as_applicant()
        
        url = reverse('sign-out')
        data = {'refresh_token': tokens['refresh']}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        
        # Verify that the token was blacklisted
        refresh_token_obj = RefreshToken(tokens['refresh'])
        blacklisted = BlacklistedToken.objects.filter(token__jti=refresh_token_obj.payload['jti']).exists()
        self.assertTrue(blacklisted)
    
    def test_sign_out_missing_token(self):
        """Test sign out without providing a refresh token"""
        self.authenticate_as_applicant()
        
        url = reverse('sign-out')
        data = {}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
