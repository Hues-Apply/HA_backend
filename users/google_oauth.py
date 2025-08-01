"""
Simple Google OAuth 2.0 implementation for HuesApply backend
Based on the pattern from: https://github.com/MomenSherif/react-oauth/issues/12
"""
import os
import json
import logging
import traceback
import requests
from django.conf import settings
from django.core.exceptions import ValidationError

# Configure logging
logger = logging.getLogger(__name__)

def exchange_code_for_tokens(code):
    """
    Exchange Google OAuth authorization code for access and refresh tokens
    """
    logger.info("Starting exchange_code_for_tokens...")

    if not code:
        logger.error("No authorization code provided")
        raise ValidationError("Authorization code is required")

    # Prepare request data
    logger.debug("Preparing request data...")
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.GOOGLE_OAUTH_REDIRECT_URI,
    }

    try:
        # Make POST request to Google token endpoint
        logger.debug("Making POST request to Google token endpoint...")
        response = requests.post(token_url, data=data, timeout=10)

        logger.debug(f"Response status: {response.status_code}")

        if response.status_code == 200:
            tokens = response.json()
            logger.info(f"Token exchange successful! Received keys: {list(tokens.keys())}")
            return tokens
        else:
            logger.error(f"Token exchange failed with status {response.status_code}: {response.text}")
            raise ValidationError(f"Token exchange failed: {response.text}")

    except requests.RequestException as e:
        logger.error(f"Network error during token exchange: {e}")
        raise ValidationError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token exchange: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise ValidationError(f"Unexpected error: {str(e)}")


def get_user_info_from_id_token(id_token):
    """
    Extract user information from Google ID token
    """
    logger.info("Starting get_user_info_from_id_token...")

    try:
        # Import Google OAuth modules
        logger.debug("Importing Google OAuth modules...")
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token

        logger.info("Google OAuth modules imported successfully")

        # Verify ID token
        logger.debug("Verifying ID token...")
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
            clock_skew_in_seconds=60
        )

        logger.info("ID token verified successfully")

        # Extract user data from ID token
        logger.debug("Extracting user data from ID token...")
        user_data = {
            'email': id_info.get('email'),
            'given_name': id_info.get('given_name', ''),
            'family_name': id_info.get('family_name', ''),
            'picture': id_info.get('picture', ''),
            'sub': id_info.get('sub'),  # Google's unique user ID
        }

        logger.info(f"User data extracted for: {user_data.get('email', 'unknown')}")
        return user_data

    except Exception as e:
        logger.error(f"Failed to decode ID token: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise ValidationError(f"Invalid ID token: {str(e)}")


def refresh_access_token(refresh_token):
    """
    Refresh Google OAuth access token using refresh token
    """
    logger.info("Starting refresh_access_token...")

    if not refresh_token:
        logger.error("No refresh token provided")
        raise ValidationError("Refresh token is required")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }

    try:
        response = requests.post(token_url, data=data, timeout=10)

        if response.status_code == 200:
            tokens = response.json()
            logger.info("Access token refreshed successfully")
            return tokens
        else:
            logger.error(f"Token refresh failed with status {response.status_code}: {response.text}")
            raise ValidationError(f"Token refresh failed: {response.text}")

    except requests.RequestException as e:
        logger.error(f"Network error during token refresh: {e}")
        raise ValidationError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise ValidationError(f"Unexpected error: {str(e)}")
