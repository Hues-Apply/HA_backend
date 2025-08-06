#!/usr/bin/env python3
"""
Debug script to test comprehensive user profile data retrieval.
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from users.models import CustomUser, EducationProfile, ExperienceProfile, ProjectsProfile
from users.serializers import ComprehensiveUserProfileSerializer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_user_profile_data(user_id=None):
    """Debug comprehensive user profile data retrieval"""
    print("=== Debugging User Profile Data ===")

    try:
        # Get a user (either by ID or first user)
        if user_id:
            user = CustomUser.objects.get(id=user_id)
        else:
            user = CustomUser.objects.first()

        if not user:
            print("❌ No users found in database")
            return False

        print(f"👤 Testing with user: {user.email} (ID: {user.id})")

        # Check if user has related data
        print("\n📊 Checking related data:")

        # Education profiles
        education_count = EducationProfile.objects.filter(user=user).count()
        print(f"   Education profiles: {education_count}")
        if education_count > 0:
            educations = EducationProfile.objects.filter(user=user)
            for edu in educations:
                print(f"     - {edu.degree} at {edu.school}")

        # Experience profiles
        experience_count = ExperienceProfile.objects.filter(user=user).count()
        print(f"   Experience profiles: {experience_count}")
        if experience_count > 0:
            experiences = ExperienceProfile.objects.filter(user=user)
            for exp in experiences:
                print(f"     - {exp.job_title} at {exp.company_name}")

        # Project profiles
        project_count = ProjectsProfile.objects.filter(user=user).count()
        print(f"   Project profiles: {project_count}")
        if project_count > 0:
            projects = ProjectsProfile.objects.filter(user=user)
            for proj in projects:
                print(f"     - {proj.project_title}")

        # Test the serializer
        print("\n🔄 Testing ComprehensiveUserProfileSerializer...")
        serializer = ComprehensiveUserProfileSerializer(user)
        data = serializer.data

        print(f"✅ Serializer data keys: {list(data.keys())}")

        # Check specific fields
        print(f"\n📋 Education profiles in serializer: {len(data.get('education_profiles', []))}")
        print(f"📋 Experience profiles in serializer: {len(data.get('experience_profiles', []))}")
        print(f"📋 Project profiles in serializer: {len(data.get('project_profiles', []))}")

        # Show education data
        if data.get('education_profiles'):
            print("\n🎓 Education data in serializer:")
            for edu in data['education_profiles']:
                print(f"   - {edu.get('degree')} at {edu.get('school')}")

        # Show experience data
        if data.get('experience_profiles'):
            print("\n💼 Experience data in serializer:")
            for exp in data['experience_profiles']:
                print(f"   - {exp.get('job_title')} at {exp.get('company_name')}")

        # Show project data
        if data.get('project_profiles'):
            print("\n🚀 Project data in serializer:")
            for proj in data['project_profiles']:
                print(f"   - {proj.get('project_title')}")

        # Test the admin endpoint
        print("\n🔄 Testing admin endpoint simulation...")
        from users.profile_views import get_user_profile_by_id
        from django.test import RequestFactory
        from rest_framework.test import force_authenticate

        factory = RequestFactory()
        request = factory.get(f'/api/profile/user/{user.id}/')

        # Simulate the admin endpoint
        response = get_user_profile_by_id(request, user.id)

        if response.status_code == 200:
            response_data = response.data
            print("✅ Admin endpoint returned success")
            print(f"📋 Response data keys: {list(response_data.keys())}")

            if 'data' in response_data:
                user_data = response_data['data']
                print(f"📋 User data keys: {list(user_data.keys())}")
                print(f"📋 Education profiles: {len(user_data.get('education_profiles', []))}")
                print(f"📋 Experience profiles: {len(user_data.get('experience_profiles', []))}")
                print(f"📋 Project profiles: {len(user_data.get('project_profiles', []))}")
        else:
            print(f"❌ Admin endpoint failed: {response.status_code}")
            print(f"Error: {response.data}")

        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

def create_test_data(user_id=None):
    """Create test data for a user"""
    print("\n=== Creating Test Data ===")

    try:
        # Get a user
        if user_id:
            user = CustomUser.objects.get(id=user_id)
        else:
            user = CustomUser.objects.first()

        if not user:
            print("❌ No users found")
            return False

        print(f"👤 Creating test data for user: {user.email}")

        # Create test education
        education, created = EducationProfile.objects.get_or_create(
            user=user,
            degree="Bachelor of Science in Computer Science",
            school="Test University",
            start_date="2020-01-01",
            end_date="2024-01-01",
            is_currently_studying=False
        )
        if created:
            print("✅ Created test education profile")
        else:
            print("ℹ️ Education profile already exists")

        # Create test experience
        experience, created = ExperienceProfile.objects.get_or_create(
            user=user,
            job_title="Software Engineer",
            company_name="Test Company",
            location="Test City",
            start_date="2024-01-01",
            is_currently_working=True,
            description="Test job description"
        )
        if created:
            print("✅ Created test experience profile")
        else:
            print("ℹ️ Experience profile already exists")

        # Create test project
        project, created = ProjectsProfile.objects.get_or_create(
            user=user,
            project_title="Test Project",
            start_date="2024-01-01",
            is_currently_working=True,
            description="Test project description"
        )
        if created:
            print("✅ Created test project profile")
        else:
            print("ℹ️ Project profile already exists")

        return True

    except Exception as e:
        print(f"❌ Failed to create test data: {e}")
        return False

def main():
    """Main debug function"""
    print("Starting profile data debugging...")

    # First, create some test data
    if create_test_data():
        print("✅ Test data created successfully")
    else:
        print("❌ Failed to create test data")

    # Then debug the data retrieval
    if debug_user_profile_data():
        print("✅ Profile data debugging completed")
    else:
        print("❌ Profile data debugging failed")

if __name__ == '__main__':
    main()
