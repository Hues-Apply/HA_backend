import os
from google.cloud import storage
from pprint import pprint
from pathlib import Path
import logging

# Load environment variables from .env file
from dotenv import load_dotenv
from .google_credentials import setup_google_credentials, get_google_credentials_info

logger = logging.getLogger(__name__)

# Get the path to the .env file in the project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Ensure Google credentials are set up
setup_google_credentials()

# Initialize the storage client (will use GOOGLE_APPLICATION_CREDENTIALS from env)
try:
    storage_client = storage.Client()
    logger.info("Google Cloud Storage client initialized successfully")
    
    # Log credential info for debugging
    creds_info = get_google_credentials_info()
    logger.info(f"Google credentials status: {creds_info['status']}")
    if creds_info.get('project_id'):
        logger.info(f"Using project: {creds_info['project_id']}")
        
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud Storage client: {e}")
    storage_client = None


def create_bucket(bucket_name: str, location: str = "US", storage_class: str = "NEARLINE"):
    """
    Creates a new bucket with given name, location and storage class.
    """
    if not storage_client:
        raise RuntimeError("Google Cloud Storage client not initialized. Check credentials setup.")
        
    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = storage_class
    bucket.location = location
    new_bucket = storage_client.create_bucket(bucket)
    print(f"Bucket {bucket_name} created.")
    pprint(vars(new_bucket))
    return new_bucket


def get_bucket(bucket_name: str):
    """
    Retrieves an existing bucket by name.
    """
    if not storage_client:
        raise RuntimeError("Google Cloud Storage client not initialized. Check credentials setup.")
        
    return storage_client.get_bucket(bucket_name)


def upload_to_bucket(blob_name: str, file_path: str, bucket_name: str):
    """
    Uploads a file to the specified bucket.

    :param blob_name: The name of the file in the bucket.
    :param file_path: Path to the file on local disk.
    :param bucket_name: The target bucket name.
    """
    bucket = get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    print(f"File {file_path} uploaded as {blob_name}.")
    return blob


def download_from_bucket(blob_name: str, file_path: str, bucket_name: str):
    """
    Downloads a file from the bucket to local disk.

    :param blob_name: The name of the file in the bucket.
    :param file_path: Path to save file locally.
    :param bucket_name: Bucket to fetch from.
    """
    bucket = get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(file_path)
    print(f"File {blob_name} downloaded to {file_path}.")


def download_from_uri(uri: str, file_path: str):
    """
    Downloads file from a GCS URI to local disk.

    :param uri: gs:// URI path
    :param file_path: Path to save file locally
    """
    if not storage_client:
        raise RuntimeError("Google Cloud Storage client not initialized. Check credentials setup.")
        
    blob = storage.Blob.from_string(uri, client=storage_client)
    blob.download_to_filename(file_path)
    print(f"File from {uri} saved to {file_path}.")


def list_buckets(max_results=50):
    """
    Lists buckets in your project.
    """
    if not storage_client:
        raise RuntimeError("Google Cloud Storage client not initialized. Check credentials setup.")
        
    print("Buckets:")
    for bucket in storage_client.list_buckets(max_results=max_results):
        print(f"- {bucket.name}")
