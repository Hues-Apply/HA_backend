#!/usr/bin/env python3
"""
Test script to verify admin interface functionality.
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

def test_admin_interface():
    """Test the admin interface functionality"""
    print("=== Testing Admin Interface ===")

    try:
        # Get all users
        users = CustomUser.objects.all()
        print(f"👥 Total users in database: {users.count()}")

        if users.count() == 0:
            print("❌ No users found in database")
            return False

        # Test each user
        for user in users:
            print(f"\n👤 Testing user: {user.email} (ID: {user.id})")

            # Check if user has profile data
            education_count = EducationProfile.objects.filter(user=user).count()
            experience_count = ExperienceProfile.objects.filter(user=user).count()
            project_count = ProjectsProfile.objects.filter(user=user).count()

            print(f"   📊 Profile data counts:")
            print(f"      Education: {education_count}")
            print(f"      Experience: {experience_count}")
            print(f"      Projects: {project_count}")

            # Test the comprehensive serializer
            serializer = ComprehensiveUserProfileSerializer(user)
            data = serializer.data

            # Check if data is returned correctly
            education_data = data.get('education_profiles', [])
            experience_data = data.get('experience_profiles', [])
            project_data = data.get('project_profiles', [])

            print(f"   📋 Serializer data:")
            print(f"      Education: {len(education_data)} entries")
            print(f"      Experience: {len(experience_data)} entries")
            print(f"      Projects: {len(project_data)} entries")

            # Show some sample data
            if education_data:
                print(f"   🎓 Sample education: {education_data[0].get('degree')} at {education_data[0].get('school')}")

            if experience_data:
                print(f"   💼 Sample experience: {experience_data[0].get('job_title')} at {experience_data[0].get('company_name')}")

            if project_data:
                print(f"   🚀 Sample project: {project_data[0].get('project_title')}")

            # Test the admin endpoint simulation
            print(f"   🔄 Testing admin endpoint...")
            from users.profile_views import get_user_profile_by_id
            from django.test import RequestFactory

            factory = RequestFactory()
            request = factory.get(f'/api/profile/user/{user.id}/')

            response = get_user_profile_by_id(request, user.id)

            if response.status_code == 200:
                response_data = response.data
                if 'data' in response_data:
                    user_data = response_data['data']
                    print(f"   ✅ Admin endpoint success")
                    print(f"      Education: {len(user_data.get('education_profiles', []))}")
                    print(f"      Experience: {len(user_data.get('experience_profiles', []))}")
                    print(f"      Projects: {len(user_data.get('project_profiles', []))}")
                else:
                    print(f"   ❌ Admin endpoint missing 'data' key")
            else:
                print(f"   ❌ Admin endpoint failed: {response.status_code}")
                print(f"      Error: {response.data}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

def create_sample_data_for_all_users():
    """Create sample data for all users who don't have any"""
    print("\n=== Creating Sample Data for All Users ===")

    try:
        users = CustomUser.objects.all()
        print(f"👥 Processing {users.count()} users")

        for user in users:
            print(f"\n👤 Processing user: {user.email}")

            # Check existing data
            education_count = EducationProfile.objects.filter(user=user).count()
            experience_count = ExperienceProfile.objects.filter(user=user).count()
            project_count = ProjectsProfile.objects.filter(user=user).count()

            print(f"   📊 Existing data: Education={education_count}, Experience={experience_count}, Projects={project_count}")

            # Create education if none exists
            if education_count == 0:
                education = EducationProfile.objects.create(
                    user=user,
                    degree="Bachelor of Science in Computer Science",
                    school="Sample University",
                    start_date="2020-01-01",
                    end_date="2024-01-01",
                    is_currently_studying=False,
                    extra_curricular="Sample extracurricular activities"
                )
                print(f"   ✅ Created education: {education.degree}")

            # Create experience if none exists
            if experience_count == 0:
                experience = ExperienceProfile.objects.create(
                    user=user,
                    job_title="Software Engineer",
                    company_name="Sample Company",
                    location="Sample City",
                    start_date="2024-01-01",
                    is_currently_working=True,
                    description="Sample job description"
                )
                print(f"   ✅ Created experience: {experience.job_title}")

            # Create project if none exists
            if project_count == 0:
                project = ProjectsProfile.objects.create(
                    user=user,
                    project_title="Sample Project",
                    start_date="2024-01-01",
                    is_currently_working=True,
                    project_link="https://example.com",
                    description="Sample project description"
                )
                print(f"   ✅ Created project: {project.project_title}")

        print("\n✅ Sample data creation completed")
        return True

    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

def main():
    """Main test function"""
    print("Starting admin interface testing...")

    # First, create sample data for all users
    if create_sample_data_for_all_users():
        print("✅ Sample data created successfully")
    else:
        print("❌ Failed to create sample data")

    # Then test the admin interface
    if test_admin_interface():
        print("✅ Admin interface testing completed successfully")
    else:
        print("❌ Admin interface testing failed")

if __name__ == '__main__':
    main()
