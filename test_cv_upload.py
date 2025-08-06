#!/usr/bin/env python3
"""
Test script to verify CV upload functionality and debug GCS upload issues.
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
from users.models import UserProfile, Document, CustomUser
from users.profile_views import SecureFileUploadMixin
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gcs_credentials():
    """Test if Google Cloud Storage credentials are properly configured"""
    print("=== Testing GCS Credentials ===")

    from utils.google_credentials import get_google_credentials_info
    creds_info = get_google_credentials_info()

    print(f"Credentials status: {creds_info['status']}")
    if creds_info.get('project_id'):
        print(f"Project ID: {creds_info['project_id']}")
    if creds_info.get('client_email'):
        print(f"Client Email: {creds_info['client_email']}")

    return creds_info['status'] == 'configured'

def test_gcs_upload():
    """Test GCS upload functionality"""
    print("\n=== Testing GCS Upload ===")

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket_name = getattr(settings, 'GCS_BUCKET_NAME', 'huesapply-user_documents')
        bucket = client.bucket(bucket_name)

        print(f"GCS Client initialized successfully")
        print(f"Bucket name: {bucket_name}")

        # Test if bucket exists
        try:
            bucket.reload()
            print(f"Bucket '{bucket_name}' exists and is accessible")
            return True
        except Exception as e:
            print(f"Bucket '{bucket_name}' not accessible: {e}")
            return False

    except Exception as e:
        print(f"Failed to initialize GCS client: {e}")
        return False

def test_file_upload_mixin():
    """Test the SecureFileUploadMixin functionality"""
    print("\n=== Testing File Upload Mixin ===")

    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%Test PDF content\n%%EOF\n')
            test_file_path = f.name

        # Create a mock file object
        class MockFile:
            def __init__(self, path):
                self.path = path
                self.name = os.path.basename(path)
                self.size = os.path.getsize(path)
                self._file = open(path, 'rb')

            def read(self, size=None):
                if size is None:
                    return self._file.read()
                return self._file.read(size)

            def seek(self, position):
                self._file.seek(position)

            def close(self):
                self._file.close()

            def __del__(self):
                if hasattr(self, '_file'):
                    self._file.close()

        mock_file = MockFile(test_file_path)

        # Test the mixin
        mixin = SecureFileUploadMixin()

        # Test file validation
        try:
            mixin.validate_file(mock_file)
            print("File validation passed")
        except Exception as e:
            print(f"File validation failed: {e}")
            return False

        # Test GCS upload
        try:
            result = mixin.upload_to_gcs(
                mock_file.read(),
                mock_file.name,
                user_id=1,
                file_type='test'
            )
            print(f"GCS upload result: {result}")
            return True
        except Exception as e:
            print(f"GCS upload failed: {e}")
            return False

    except Exception as e:
        print(f"Test failed: {e}")
        return False
    finally:
        # Cleanup
        if 'test_file_path' in locals():
            try:
                os.unlink(test_file_path)
            except:
                pass

def test_user_profile_cv_fields():
    """Test UserProfile CV fields"""
    print("\n=== Testing UserProfile CV Fields ===")

    try:
        # Get or create a test user
        user, created = CustomUser.objects.get_or_create(
            email='test@example.com',
            defaults={'first_name': 'Test', 'last_name': 'User'}
        )

        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={}
        )

        # Test CV fields
        print(f"Profile CV filename: {profile.cv_filename}")
        print(f"Profile CV GCS path: {profile.cv_gcs_path}")
        print(f"Profile CV public URL: {profile.cv_public_url}")
        print(f"Profile has CV in GCS: {profile.has_cv_in_gcs()}")
        print(f"Profile CV download URL: {profile.get_cv_download_url()}")

        return True

    except Exception as e:
        print(f"UserProfile test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting CV upload tests...")

    tests = [
        ("GCS Credentials", test_gcs_credentials),
        ("GCS Upload", test_gcs_upload),
        ("File Upload Mixin", test_file_upload_mixin),
        ("UserProfile CV Fields", test_user_profile_cv_fields),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    print("\n=== Test Results ===")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

    return all_passed

if __name__ == '__main__':
    main()
