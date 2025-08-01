import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import UserProfile, Document, ParsedProfile, UserGoal
from .serializers import UserRegistrationSerializer

User = get_user_model()


class UserModelTestCase(TestCase):
    """Test cases for User model"""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_creation(self):
        """Test user creation"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_role_default(self):
        """Test default user role"""
        self.assertEqual(self.user.get_role(), 'applicant')
        self.assertTrue(self.user.is_applicant())
        self.assertFalse(self.user.is_employer())

    def test_user_role_changes(self):
        """Test user role changes"""
        self.user.set_as_employer()
        self.assertEqual(self.user.get_role(), 'employer')
        self.assertTrue(self.user.is_employer())
        self.assertFalse(self.user.is_applicant())

        self.user.set_as_applicant()
        self.assertEqual(self.user.get_role(), 'applicant')
        self.assertTrue(self.user.is_applicant())
        self.assertFalse(self.user.is_employer())


class UserProfileTestCase(TestCase):
    """Test cases for UserProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def test_profile_creation(self):
        """Test profile creation"""
        self.assertEqual(self.profile.user, self.user)
        self.assertIsNotNone(self.profile.created_at)

    def test_profile_str_representation(self):
        """Test profile string representation"""
        self.assertEqual(str(self.profile), f"Profile for {self.user.email}")


class UserRegistrationSerializerTestCase(TestCase):
    """Test cases for UserRegistrationSerializer"""

    def test_valid_registration_data(self):
        """Test valid registration data"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'applicant'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_email(self):
        """Test invalid email format"""
        data = {
            'email': 'invalid-email',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_password_mismatch(self):
        """Test password confirmation mismatch"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


class UserAPITestCase(APITestCase):
    """Test cases for User API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def test_user_role_api_get(self):
        """Test getting user role"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-role'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'applicant')

    def test_user_role_api_post(self):
        """Test updating user role"""
        self.client.force_authenticate(user=self.user)
        data = {'role': 'employer'}
        response = self.client.post(reverse('user-role'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_role(), 'employer')

    def test_user_role_api_invalid_role(self):
        """Test invalid role update"""
        self.client.force_authenticate(user=self.user)
        data = {'role': 'invalid_role'}
        response = self.client.post(reverse('user-role'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GoogleOAuthTestCase(APITestCase):
    """Test cases for Google OAuth endpoints"""

    def setUp(self):
        self.client = APIClient()

    @patch('users.views.GOOGLE_OAUTH_AVAILABLE', True)
    @patch('users.views.exchange_code_for_tokens')
    @patch('users.views.get_user_info_from_id_token')
    def test_google_auth_callback_success(self, mock_get_user_info, mock_exchange_tokens):
        """Test successful Google OAuth callback"""
        # Mock the OAuth functions
        mock_exchange_tokens.return_value = {'id_token': 'mock_id_token'}
        mock_get_user_info.return_value = {
            'email': 'google@example.com',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True
        }

        data = {'code': 'mock_auth_code'}
        response = self.client.post(reverse('google-auth-callback'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access_token', response.data['data'])
        self.assertIn('user', response.data['data'])

    def test_google_auth_callback_no_code(self):
        """Test Google OAuth callback without code"""
        data = {}
        response = self.client.post(reverse('google-auth-callback'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('users.views.GOOGLE_OAUTH_AVAILABLE', False)
    def test_google_auth_callback_unavailable(self):
        """Test Google OAuth when service is unavailable"""
        data = {'code': 'mock_auth_code'}
        response = self.client.post(reverse('google-auth-callback'), data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class DocumentUploadTestCase(APITestCase):
    """Test cases for document upload functionality"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_document_upload_success(self):
        """Test successful document upload"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create a mock PDF file
        pdf_content = b'%PDF-1.4\n%Test PDF content'
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )

        data = {
            'file': pdf_file,
            'document_type': 'resume'
        }

        response = self.client.post(reverse('document-upload'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_document_upload_no_file(self):
        """Test document upload without file"""
        data = {'document_type': 'resume'}
        response = self.client.post(reverse('document-upload'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserGoalTestCase(TestCase):
    """Test cases for UserGoal model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_goal_creation(self):
        """Test goal creation"""
        goal = UserGoal.objects.create(
            user=self.user,
            goal='Find a software engineering job',
            priority=1
        )
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.goal, 'Find a software engineering job')
        self.assertEqual(goal.priority, 1)

    def test_goal_ordering(self):
        """Test goal ordering by priority"""
        goal1 = UserGoal.objects.create(user=self.user, goal='Goal 1', priority=2)
        goal2 = UserGoal.objects.create(user=self.user, goal='Goal 2', priority=1)

        goals = UserGoal.objects.filter(user=self.user).order_by('priority')
        self.assertEqual(goals[0], goal2)
        self.assertEqual(goals[1], goal1)


class ParsedProfileTestCase(TestCase):
    """Test cases for ParsedProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.parsed_profile = ParsedProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            confidence_score=0.85
        )

    def test_parsed_profile_creation(self):
        """Test parsed profile creation"""
        self.assertEqual(self.parsed_profile.user, self.user)
        self.assertEqual(self.parsed_profile.first_name, 'Test')
        self.assertEqual(self.parsed_profile.confidence_score, Decimal('0.85'))

    def test_completion_percentage_calculation(self):
        """Test completion percentage calculation"""
        # Initially should be low since most fields are empty
        self.assertLess(self.parsed_profile.completion_percentage, 50)

        # Fill in more fields
        self.parsed_profile.summary = 'Test summary'
        self.parsed_profile.skills = ['Python', 'Django']
        self.parsed_profile.save()

        # Should have higher completion percentage
        self.assertGreater(self.parsed_profile.completion_percentage, 50)


class SecurityTestCase(APITestCase):
    """Test cases for security features"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        response = self.client.get(reverse('user-role'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_input_sanitization(self):
        """Test input sanitization"""
        self.client.force_authenticate(user=self.user)

        # Test with potentially malicious input
        malicious_data = {
            'role': '<script>alert("xss")</script>employer'
        }

        response = self.client.post(reverse('user-role'), malicious_data)
        # Should still work but with sanitized input
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_role(), 'employer')


class RateLimitingTestCase(APITestCase):
    """Test cases for rate limiting"""

    def setUp(self):
        self.client = APIClient()

    def test_rate_limiting_on_public_endpoints(self):
        """Test rate limiting on public endpoints"""
        # Make multiple requests to test rate limiting
        for _ in range(10):
            response = self.client.get(reverse('google-client-id'))
            # Should not hit rate limit for reasonable number of requests
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class HealthCheckTestCase(APITestCase):
    """Test cases for health check endpoint"""

    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('cache', response.data)
