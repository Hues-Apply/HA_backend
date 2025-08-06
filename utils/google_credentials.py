"""
Google Cloud credentials setup utility for Vercel deployment.
Handles base64-encoded service account credentials.
"""
import os
import base64
import tempfile
import json
import logging

logger = logging.getLogger(__name__)


def setup_google_credentials():
    """
    Set up Google Cloud credentials from base64-encoded environment variable.
    This is useful for Vercel deployment where the service account JSON
    needs to be base64-encoded in environment variables.
    """
    # Check if GOOGLE_APPLICATION_CREDENTIALS is already set and file exists
    existing_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if existing_credentials and os.path.exists(existing_credentials):
        logger.info(f"Google credentials already configured: {existing_credentials}")
        return existing_credentials

    # Try to get base64 credentials from environment
    b64_credentials = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    
    if not b64_credentials:
        # Fallback to local development setup
        local_creds_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "hues-apply-docs-30393bf1931c.json")
        if os.path.exists(local_creds_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_creds_path
            logger.info(f"Using local Google credentials: {local_creds_path}")
            return local_creds_path
        else:
            logger.warning("No Google credentials found (neither base64 nor local file)")
            return None

    try:
        # Decode base64 credentials
        credentials_data = base64.b64decode(b64_credentials)
        
        # Validate it's valid JSON
        json.loads(credentials_data)
        
        # Create temporary file for credentials
        # Use /tmp for Vercel, or system temp directory for local development
        temp_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
        credentials_path = os.path.join(temp_dir, "gcp_credentials.json")
        
        # Write decoded credentials to temporary file
        with open(credentials_path, "wb") as f:
            f.write(credentials_data)
        
        # Set environment variable for Google SDK
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        logger.info(f"Google credentials decoded and saved to: {credentials_path}")
        return credentials_path
        
    except base64.binascii.Error as e:
        logger.error(f"Failed to decode base64 Google credentials: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in decoded Google credentials: {e}")
        return None
    except Exception as e:
        logger.error(f"Error setting up Google credentials: {e}")
        return None


def get_google_credentials_info():
    """
    Get information about currently configured Google credentials.
    Useful for debugging and verification.
    """
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not credentials_path:
        return {"status": "not_configured", "path": None}
    
    if not os.path.exists(credentials_path):
        return {"status": "file_not_found", "path": credentials_path}
    
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        return {
            "status": "configured",
            "path": credentials_path,
            "project_id": creds_data.get("project_id"),
            "client_email": creds_data.get("client_email"),
            "type": creds_data.get("type")
        }
    except Exception as e:
        return {"status": "error", "path": credentials_path, "error": str(e)}
