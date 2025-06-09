"""
Tests for applications API endpoints
"""
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from tests.test_utils import BaseAPITestCase
from opportunities.models import Opportunity, Category
from applications.models import Application


class ApplicationsAPITests(BaseAPITestCase):
    """Test applications API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create a category and opportunity
        self.category = Category.objects.create(name='Technology', slug='technology')
        self.opportunity = Opportunity.objects.create(
            title='Software Engineer',
            type='job',
            organization='Tech Company',
            description='Looking for a Python developer',
            location='New York',
            is_remote=True,
            deadline=timezone.now().date() + timezone.timedelta(days=30),
            category=self.category,
            posted_by=self.employer_user
        )
    
    def test_create_application(self):
        """Test creating a new application"""
        self.authenticate_as_applicant()
        
        url = reverse('application-create')
        data = {
            'opportunity': self.opportunity.id,
            'cover_letter': 'I am interested in this position.',
            'resume': 'https://example.com/resume.pdf',
            'additional_info': {'years_experience': 5}
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        # Check that the application was created in the database
        application = Application.objects.get(id=response.data['id'])
        self.assertEqual(application.user, self.applicant_user)
        self.assertEqual(application.opportunity, self.opportunity)
    
    def test_list_user_applications(self):
        """Test listing user's applications"""
        self.authenticate_as_applicant()
        
        # Create an application first
        application = Application.objects.create(
            user=self.applicant_user,
            opportunity=self.opportunity,
            cover_letter='I am interested in this position.',
            resume='https://example.com/resume.pdf',
            status='pending'
        )
        
        url = reverse('user-applications')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], application.id)
    
    def test_list_opportunity_applications(self):
        """Test listing applications for an opportunity"""
        self.authenticate_as_employer()
        
        # Create an application first
        application = Application.objects.create(
            user=self.applicant_user,
            opportunity=self.opportunity,
            cover_letter='I am interested in this position.',
            resume='https://example.com/resume.pdf',
            status='pending'
        )
        
        url = reverse('opportunity-applications', kwargs={'opportunity_id': self.opportunity.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], application.id)
    
    def test_update_application_status(self):
        """Test updating an application status"""
        self.authenticate_as_employer()
        
        # Create an application first
        application = Application.objects.create(
            user=self.applicant_user,
            opportunity=self.opportunity,
            cover_letter='I am interested in this position.',
            resume='https://example.com/resume.pdf',
            status='pending'
        )
        
        url = reverse('update-application-status', kwargs={'pk': application.id})
        data = {'status': 'accepted'}
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the status was updated
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')
    
    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access application data"""
        # Create an application
        application = Application.objects.create(
            user=self.applicant_user,
            opportunity=self.opportunity,
            cover_letter='I am interested in this position.',
            resume='https://example.com/resume.pdf',
            status='pending'
        )
        
        # Unauthenticated user should not access applications
        url = reverse('user-applications')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Applicant user should not access other employer's opportunity applications
        self.authenticate_as_applicant()
        url = reverse('opportunity-applications', kwargs={'opportunity_id': self.opportunity.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
