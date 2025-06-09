"""
Tests for user API endpoints
"""
from django.urls import reverse
from rest_framework import status

from tests.test_utils import BaseAPITestCase
from users.models import UserProfile


class UserRoleAPITests(BaseAPITestCase):
    """Test user role API endpoints"""
    
    def test_get_user_role_as_applicant(self):
        """Test retrieving user role as an applicant"""
        self.authenticate_as_applicant()
        
        url = reverse('user-role')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'Applicant')
        self.assertTrue(response.data['is_applicant'])
        self.assertFalse(response.data['is_employer'])
        self.assertFalse(response.data['is_admin'])
    
    def test_get_user_role_as_employer(self):
        """Test retrieving user role as an employer"""
        self.authenticate_as_employer()
        
        url = reverse('user-role')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'Employer')
        self.assertFalse(response.data['is_applicant'])
        self.assertTrue(response.data['is_employer'])
        self.assertFalse(response.data['is_admin'])
    
    def test_get_user_role_as_admin(self):
        """Test retrieving user role as an admin"""
        self.authenticate_as_admin()
        
        url = reverse('user-role')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('role', response.data)
        self.assertIn('is_admin', response.data)
        self.assertTrue(response.data['is_admin'])
    
    def test_get_role_unauthenticated(self):
        """Test that unauthenticated users cannot access role endpoint"""
        url = reverse('user-role')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_role_to_employer(self):
        """Test updating user role to employer"""
        self.authenticate_as_applicant()
        
        url = reverse('user-role')
        data = {'role': 'employer'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('Employer', response.data['message'])
        
        # Verify the user's role was updated
        self.applicant_user.refresh_from_db()
        self.assertTrue(self.applicant_user.is_employer())
        self.assertFalse(self.applicant_user.is_applicant())
    
    def test_update_role_to_applicant(self):
        """Test updating user role to applicant"""
        self.authenticate_as_employer()
        
        url = reverse('user-role')
        data = {'role': 'applicant'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('Applicant', response.data['message'])
        
        # Verify the user's role was updated
        self.employer_user.refresh_from_db()
        self.assertTrue(self.employer_user.is_applicant())
        self.assertFalse(self.employer_user.is_employer())
    
    def test_update_role_invalid(self):
        """Test updating user role with an invalid role"""
        self.authenticate_as_applicant()
        
        url = reverse('user-role')
        data = {'role': 'invalid_role'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
