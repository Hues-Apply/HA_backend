"""
Tests for opportunity recommendations API endpoints
"""
from django.urls import reverse
from rest_framework import status

from tests.test_utils import BaseAPITestCase
from tests.opportunities.test_opportunities_api import OpportunityAPITestCase
from users.models import UserProfile


class RecommendationAPITests(OpportunityAPITestCase):
    """Test opportunity recommendation API endpoints"""
    
    def setUp(self):
        """Set up test data including user profiles with skills"""
        super().setUp()
        
        # Create user profile with skills for the applicant user
        self.profile = UserProfile.objects.create(
            user=self.applicant_user,
            name='Applicant User',
            email=self.applicant_user.email,
            profile_picture='https://example.com/picture.jpg',
            skills=['Python', 'Django', 'JavaScript'],
            education={
                'highest_level': 'bachelors',
                'age': 25,
                'nationality': 'Nigerian'
            },
            preferences={
                'preferred_type': 'job',
                'preferred_category': 'technology'
            },
            location='New York'
        )
        
        # Update job opportunity with matching skills
        self.job_opportunity.skills_required = ['Python', 'Django']
        self.job_opportunity.save()
    
    def test_get_recommended_opportunities(self):
        """Test retrieving recommended opportunities"""
        self.authenticate_as_applicant()
        
        url = reverse('recommended-opportunities')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # There should be at least one recommendation (the job opportunity)
        self.assertGreater(len(response.data['results']), 0)
        
        # The job opportunity should have a high match score due to skill match
        job_in_results = False
        for result in response.data['results']:
            if result['opportunity']['id'] == self.job_opportunity.id:
                job_in_results = True
                self.assertIn('score', result)
                self.assertIn('match_reasons', result)
                
        self.assertTrue(job_in_results, "Job opportunity should be in recommendations")
    
    def test_filter_recommendations_by_type(self):
        """Test filtering recommendations by opportunity type"""
        self.authenticate_as_applicant()
        
        url = reverse('recommended-opportunities')
        response = self.client.get(url, {'type': 'scholarship'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that all results are of type scholarship
        for result in response.data['results']:
            self.assertEqual(result['opportunity']['type'], 'scholarship')
    
    def test_recommendations_require_authentication(self):
        """Test that recommendations require authentication"""
        url = reverse('recommended-opportunities')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
