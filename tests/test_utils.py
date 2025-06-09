"""
Base test cases and utilities for API testing
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import CustomUser


class BaseAPITestCase(APITestCase):
    """
    Base test case for API tests with authentication helpers
    """
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        self.applicant_user = CustomUser.objects.create_user(
            email='applicant@example.com',
            password='userpass123',
            first_name='Applicant',
            last_name='User'
        )
        self.applicant_user.set_as_applicant()
        
        self.employer_user = CustomUser.objects.create_user(
            email='employer@example.com',
            password='userpass123',
            first_name='Employer',
            last_name='User'
        )
        self.employer_user.set_as_employer()
        
    def get_tokens_for_user(self, user):
        """Generate JWT tokens for a user"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def authenticate_client(self, user):
        """Authenticate client with the specified user"""
        tokens = self.get_tokens_for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return tokens
    
    def authenticate_as_admin(self):
        """Authenticate as admin user"""
        return self.authenticate_client(self.admin_user)
    
    def authenticate_as_applicant(self):
        """Authenticate as applicant user"""
        return self.authenticate_client(self.applicant_user)
    
    def authenticate_as_employer(self):
        """Authenticate as employer user"""
        return self.authenticate_client(self.employer_user)
    
    def clear_authentication(self):
        """Clear authentication credentials"""
        self.client.credentials()


def api_reverse(view_name, **kwargs):
    """Shortcut for reverse with a consistent /api/ prefix"""
    return reverse(view_name, kwargs=kwargs)
