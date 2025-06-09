from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from opportunities.models import Opportunity, Category, Tag
from opportunities.matching import OpportunityMatcher
from users.models import UserProfile

class MockUserProfile:
    """Mock user profile for testing"""
    def __init__(self):
        self.user = type('obj', (object,), {'id': 1})
        self.skills = ['Python', 'Django', 'JavaScript']
        self.education = {
            'highest_level': 'bachelors',
            'age': 25,
            'nationality': 'Nigerian'
        }
        self.preferences = {
            'preferred_type': 'job',
            'preferred_category': 'technology'
        }
        self.location = 'Lagos, Nigeria'

class MatchingAlgorithmTests(TestCase):
    def setUp(self):
        # Create test data
        tech_category = Category.objects.create(name='Technology', slug='technology')
        health_category = Category.objects.create(name='Healthcare', slug='healthcare')
        
        python_tag = Tag.objects.create(name='Python', slug='python')
        django_tag = Tag.objects.create(name='Django', slug='django')
        js_tag = Tag.objects.create(name='JavaScript', slug='javascript')
        
        # Create a perfect match opportunity
        self.perfect_match = Opportunity.objects.create(
            title='Python Developer',
            type='job',
            organization='Tech Company',
            category=tech_category,
            location='Lagos, Nigeria',
            is_remote=False,
            description='Looking for a Python developer',
            eligibility_criteria={
                'education_level': 'bachelors',
                'min_age': 18,
                'max_age': 40,
                'nationalities': ['Nigerian', 'Ghanaian']
            },
            skills_required=['Python', 'Django'],
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.perfect_match.tags.add(python_tag, django_tag)
        
        # Create a partial match opportunity
        self.partial_match = Opportunity.objects.create(
            title='Frontend Developer',
            type='job',
            organization='Another Company',
            category=tech_category,
            location='Accra, Ghana',
            is_remote=True,
            description='Looking for a frontend developer',
            eligibility_criteria={
                'education_level': 'bachelors',
                'min_age': 18,
                'max_age': 40
            },
            skills_required=['JavaScript', 'React'],
            deadline=timezone.now().date() + timedelta(days=30)
        )
        self.partial_match.tags.add(js_tag)
        
        # Create a non-match opportunity
        self.non_match = Opportunity.objects.create(
            title='Doctor',
            type='job',
            organization='Hospital',
            category=health_category,
            location='London, UK',
            is_remote=False,
            description='Looking for a doctor',
            eligibility_criteria={
                'education_level': 'phd',
                'min_age': 30,
                'max_age': 60
            },
            skills_required=['Medicine', 'Surgery'],
            deadline=timezone.now().date() + timedelta(days=30)
        )
        
        self.user_profile = MockUserProfile()
        
    def test_opportunity_matching(self):
        matcher = OpportunityMatcher(self.user_profile)
        recommendations = matcher.get_recommended_opportunities()
        
        # Check order of recommendations
        self.assertEqual(recommendations[0]['opportunity'].id, self.perfect_match.id)
        self.assertEqual(recommendations[1]['opportunity'].id, self.partial_match.id)
        self.assertEqual(recommendations[2]['opportunity'].id, self.non_match.id)
