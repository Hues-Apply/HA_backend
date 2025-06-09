"""
Tests for opportunity listing and filtering API endpoints
"""
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from tests.test_utils import BaseAPITestCase
from opportunities.models import Opportunity, Category, Tag


class OpportunityAPITestCase(BaseAPITestCase):
    """Base test case for opportunity API tests with common setup"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        # Create categories
        self.tech_category = Category.objects.create(name='Technology', slug='technology')
        self.health_category = Category.objects.create(name='Healthcare', slug='healthcare')
        self.education_category = Category.objects.create(name='Education', slug='education')
        
        # Create tags
        self.python_tag = Tag.objects.create(name='Python', slug='python')
        self.js_tag = Tag.objects.create(name='JavaScript', slug='javascript')
        self.remote_tag = Tag.objects.create(name='Remote', slug='remote')
        
        # Create opportunities
        self.job_opportunity = Opportunity.objects.create(
            title='Software Engineer',
            type='job',
            organization='Tech Company',
            description='Looking for a Python developer',
            location='New York',
            is_remote=True,
            deadline=timezone.now().date() + timedelta(days=30),
            category=self.tech_category,
            posted_by=self.employer_user
        )
        self.job_opportunity.tags.add(self.python_tag)
        
        self.scholarship_opportunity = Opportunity.objects.create(
            title='CS Scholarship',
            type='scholarship',
            organization='University XYZ',
            description='Scholarship for CS students',
            location='Boston',
            is_remote=False,
            deadline=timezone.now().date() + timedelta(days=60),
            category=self.education_category,
            posted_by=self.employer_user
        )
        
        self.grant_opportunity = Opportunity.objects.create(
            title='Research Grant',
            type='grant',
            organization='Health Institute',
            description='Grant for health research',
            location='Remote',
            is_remote=True,
            deadline=timezone.now().date() + timedelta(days=15),
            category=self.health_category,
            posted_by=self.employer_user
        )
        self.grant_opportunity.tags.add(self.remote_tag)
        
        self.expired_opportunity = Opportunity.objects.create(
            title='Expired Internship',
            type='internship',
            organization='Old Corp',
            description='This opportunity has expired',
            location='Chicago',
            is_remote=False,
            deadline=timezone.now().date() - timedelta(days=5),
            category=self.tech_category,
            posted_by=self.employer_user
        )


class OpportunityListingAPITests(OpportunityAPITestCase):
    """Test opportunity listing and filtering API endpoints"""
    
    def test_list_opportunities(self):
        """Test listing all opportunities"""
        url = reverse('opportunity-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return non-expired opportunities by default
        self.assertEqual(response.data['count'], 3)
    
    def test_list_opportunities_with_expired(self):
        """Test listing all opportunities including expired ones"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'show_expired': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
    
    def test_filter_by_type(self):
        """Test filtering opportunities by type"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'type': 'job'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['type'], 'job')
    
    def test_filter_by_location(self):
        """Test filtering opportunities by location"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'location': 'New York'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['location'], 'New York')
    
    def test_filter_by_remote(self):
        """Test filtering opportunities by remote status"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'is_remote': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for result in response.data['results']:
            self.assertTrue(result['is_remote'])
    
    def test_filter_by_category(self):
        """Test filtering opportunities by category"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'category__slug': 'technology'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['category']['slug'], 'technology')
    
    def test_filter_by_tag(self):
        """Test filtering opportunities by tag"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'tags__slug': 'python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
    
    def test_search_opportunities(self):
        """Test searching opportunities"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'search': 'python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Software Engineer')
    
    def test_ordering_opportunities(self):
        """Test ordering opportunities"""
        url = reverse('opportunity-list')
        response = self.client.get(url, {'ordering': 'deadline'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Research Grant')
        
        # Test reverse ordering
        response = self.client.get(url, {'ordering': '-deadline'})
        self.assertEqual(response.data['results'][0]['title'], 'CS Scholarship')


class OpportunityDetailAPITests(OpportunityAPITestCase):
    """Test opportunity detail API endpoint"""
    
    def test_get_opportunity_detail(self):
        """Test retrieving opportunity details"""
        url = reverse('opportunity-detail', kwargs={'pk': self.job_opportunity.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.job_opportunity.pk)
        self.assertEqual(response.data['title'], 'Software Engineer')
        self.assertEqual(response.data['organization'], 'Tech Company')
        self.assertTrue('tags' in response.data)
        
    def test_get_nonexistent_opportunity(self):
        """Test retrieving a non-existent opportunity"""
        url = reverse('opportunity-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
