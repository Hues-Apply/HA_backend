"""
Tests for opportunity tracking API endpoints
"""
from django.urls import reverse
from rest_framework import status

from tests.test_utils import BaseAPITestCase
from tests.opportunities.test_opportunities_api import OpportunityAPITestCase
from opportunities.models import OpportunityView, OpportunityApplication


class TrackingAPITests(OpportunityAPITestCase):
    """Test opportunity tracking API endpoints"""
    
    def test_track_view(self):
        """Test tracking an opportunity view"""
        url = reverse('track-view', kwargs={'pk': self.job_opportunity.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('view_count', response.data)
        
        # Check that the view was recorded in the database
        self.assertTrue(OpportunityView.objects.filter(opportunity=self.job_opportunity).exists())
    
    def test_track_application(self):
        """Test tracking an opportunity application"""
        self.authenticate_as_applicant()
        
        url = reverse('track-application', kwargs={'pk': self.job_opportunity.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('application_count', response.data)
        
        # Check that the application was recorded in the database
        self.assertTrue(OpportunityApplication.objects.filter(
            opportunity=self.job_opportunity,
            user=self.applicant_user
        ).exists())
    
    def test_track_application_unauthenticated(self):
        """Test that unauthenticated users cannot track applications"""
        url = reverse('track-application', kwargs={'pk': self.job_opportunity.pk})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_track_nonexistent_opportunity(self):
        """Test tracking a non-existent opportunity"""
        url = reverse('track-view', kwargs={'pk': 9999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
