#!/usr/bin/env python3
"""
Debug script to test GCS upload with detailed error reporting.
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
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_gcs_upload():
    """Debug GCS upload with detailed error reporting"""
    print("=== Debugging GCS Upload ===")

    try:
        from google.cloud import storage
        print("✅ Google Cloud Storage library imported successfully")

        # Test credentials
        from utils.google_credentials import get_google_credentials_info
        creds_info = get_google_credentials_info()
        print(f"📋 Credentials status: {creds_info['status']}")
        if creds_info.get('project_id'):
            print(f"📋 Project ID: {creds_info['project_id']}")
        if creds_info.get('client_email'):
            print(f"📋 Client Email: {creds_info['client_email']}")

        # Initialize client
        print("🔄 Initializing GCS client...")
        client = storage.Client()
        print("✅ GCS client initialized successfully")

        # Get bucket
        bucket_name = getattr(settings, 'GCS_BUCKET_NAME', 'huesapply-user_documents')
        print(f"🔄 Getting bucket: {bucket_name}")
        bucket = client.bucket(bucket_name)

        # Test bucket access
        print("🔄 Testing bucket access...")
        try:
            bucket.reload()
            print("✅ Bucket exists and is accessible")
        except Exception as e:
            print(f"❌ Bucket access failed: {e}")
            return False

        # Test upload
        print("🔄 Testing file upload...")
        test_content = b'Test PDF content for GCS upload'
        test_filename = 'test_upload.pdf'

        # Generate unique filename
        import uuid
        unique_filename = f"test/1/{uuid.uuid4()}.pdf"
        print(f"📁 Uploading to: {unique_filename}")

        # Create blob and upload
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(test_content, content_type='application/pdf')
        print("✅ File uploaded successfully")

        # Test public URL
        public_url = blob.public_url
        print(f"🔗 Public URL: {public_url}")

        # Clean up test file
        print("🔄 Cleaning up test file...")
        blob.delete()
        print("✅ Test file deleted")

        return True

    except ImportError as e:
        print(f"❌ Failed to import Google Cloud Storage: {e}")
        return False
    except Exception as e:
        print(f"❌ GCS upload test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

def test_upload_mixin():
    """Test the SecureFileUploadMixin"""
    print("\n=== Testing SecureFileUploadMixin ===")

    try:
        from users.profile_views import SecureFileUploadMixin

        # Create test file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%Test PDF content\n%%EOF\n')
            test_file_path = f.name

        # Create mock file object
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
        print("🔄 Testing file validation...")
        try:
            mixin.validate_file(mock_file)
            print("✅ File validation passed")
        except Exception as e:
            print(f"❌ File validation failed: {e}")
            return False

        # Test GCS upload
        print("🔄 Testing GCS upload through mixin...")
        try:
            result = mixin.upload_to_gcs(
                mock_file.read(),
                mock_file.name,
                user_id=1,
                file_type='test'
            )
            print(f"✅ GCS upload result: {result}")
            return True
        except Exception as e:
            print(f"❌ GCS upload failed: {e}")
            import traceback
            print(f"📋 Full traceback: {traceback.format_exc()}")
            return False

    except Exception as e:
        print(f"❌ Mixin test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False
    finally:
        # Cleanup
        if 'test_file_path' in locals():
            try:
                os.unlink(test_file_path)
            except:
                pass

def main():
    """Run all debug tests"""
    print("Starting GCS upload debugging...")

    tests = [
        ("GCS Upload", debug_gcs_upload),
        ("Upload Mixin", test_upload_mixin),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))

    print("\n=== Debug Results ===")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")

    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

    return all_passed

if __name__ == '__main__':
    main()
