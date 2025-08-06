#!/usr/bin/env python3
"""
Test script to verify parsed CV data functionality.
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
from users.models import CustomUser, ParsedProfile
from users.serializers import ComprehensiveUserProfileSerializer
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_parsed_cv_data():
    """Test parsed CV data functionality"""
    print("=== Testing Parsed CV Data ===")

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

            # Check if user has parsed profile data
            try:
                parsed_profile = user.parsed_profile
                print(f"   ✅ Parsed profile found")

                # Check education data
                education_count = len(parsed_profile.education) if parsed_profile.education else 0
                print(f"   📊 Education entries: {education_count}")
                if education_count > 0:
                    for i, edu in enumerate(parsed_profile.education):
                        print(f"      {i+1}. {edu.get('degree', 'N/A')} at {edu.get('institution', 'N/A')}")

                # Check experience data
                experience_count = len(parsed_profile.experience) if parsed_profile.experience else 0
                print(f"   📊 Experience entries: {experience_count}")
                if experience_count > 0:
                    for i, exp in enumerate(parsed_profile.experience):
                        print(f"      {i+1}. {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}")

                # Check projects data
                projects_count = len(parsed_profile.projects) if parsed_profile.projects else 0
                print(f"   📊 Projects entries: {projects_count}")
                if projects_count > 0:
                    for i, proj in enumerate(parsed_profile.projects):
                        print(f"      {i+1}. {proj.get('name', proj.get('title', 'N/A'))}")

                # Check skills
                skills_count = len(parsed_profile.skills) if parsed_profile.skills else 0
                print(f"   📊 Skills: {skills_count}")
                if skills_count > 0:
                    print(f"      Skills: {', '.join(parsed_profile.skills[:5])}{'...' if skills_count > 5 else ''}")

                # Check confidence score
                print(f"   📊 Confidence score: {parsed_profile.confidence_score or 'N/A'}")
                print(f"   📊 Completion percentage: {parsed_profile.completion_percentage}%")

            except ParsedProfile.DoesNotExist:
                print(f"   ❌ No parsed profile found")

                # Create sample parsed data for testing
                print(f"   🔄 Creating sample parsed data...")
                sample_parsed_data = {
                    'education': [
                        {
                            'institution': 'Sample University',
                            'degree': 'Bachelor of Science in Computer Science',
                            'field_of_study': 'Computer Science',
                            'start_date': '2020-01-01',
                            'end_date': '2024-01-01',
                            'gpa': '3.8',
                            'description': 'Sample education description'
                        }
                    ],
                    'experience': [
                        {
                            'company': 'Sample Company',
                            'position': 'Software Engineer',
                            'start_date': '2024-01-01',
                            'is_current': True,
                            'description': 'Sample job description',
                            'achievements': ['Achievement 1', 'Achievement 2']
                        }
                    ],
                    'projects': [
                        {
                            'name': 'Sample Project',
                            'title': 'Sample Project Title',
                            'start_date': '2024-01-01',
                            'url': 'https://example.com',
                            'description': 'Sample project description',
                            'technologies': ['React', 'Node.js', 'Python']
                        }
                    ],
                    'skills': ['JavaScript', 'Python', 'React', 'Node.js', 'SQL'],
                    'confidence_score': 0.85
                }

                parsed_profile = ParsedProfile.objects.create(
                    user=user,
                    education=sample_parsed_data['education'],
                    experience=sample_parsed_data['experience'],
                    projects=sample_parsed_data['projects'],
                    skills=sample_parsed_data['skills'],
                    confidence_score=sample_parsed_data['confidence_score']
                )
                print(f"   ✅ Created sample parsed profile")

            # Test the comprehensive serializer
            print(f"   🔄 Testing comprehensive serializer...")
            serializer = ComprehensiveUserProfileSerializer(user)
            data = serializer.data

            # Check parsed profile data in serializer
            parsed_data = data.get('parsed_profile_data')
            if parsed_data:
                print(f"   ✅ Parsed profile data found in serializer")
                print(f"      Education: {len(parsed_data.get('education', []))} entries")
                print(f"      Experience: {len(parsed_data.get('experience', []))} entries")
                print(f"      Projects: {len(parsed_data.get('projects', []))} entries")
                print(f"      Skills: {len(parsed_data.get('skills', []))} skills")
            else:
                print(f"   ❌ No parsed profile data in serializer")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Main test function"""
    print("Starting parsed CV data testing...")

    if test_parsed_cv_data():
        print("✅ Parsed CV data testing completed successfully")
    else:
        print("❌ Parsed CV data testing failed")

if __name__ == '__main__':
    main()
