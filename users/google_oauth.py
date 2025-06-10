"""
Simple Google OAuth 2.0 implementation for HuesApply backend
Based on the pattern from: https://github.com/MomenSherif/react-oauth/issues/12
"""
import requests
import logging
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

def exchange_code_for_tokens(code):
    """
    Simple implementation to exchange Google OAuth code for tokens
    Similar to: const { tokens } = await oAuth2Client.getToken(req.body.code);
    """
    print("🔍 [OAUTH] Starting exchange_code_for_tokens...")
    try:
        # Google's token endpoint
        token_url = 'https://oauth2.googleapis.com/token'
        
        print("🔍 [OAUTH] Preparing request data...")
        # Prepare the request data
        data = {
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': 'postmessage',  # For web apps using popup/postMessage
            'grant_type': 'authorization_code'
        }
        
        print("🔍 [OAUTH] Making POST request to Google token endpoint...")
        # Exchange code for tokens
        response = requests.post(token_url, data=data)
        
        print(f"🔍 [OAUTH] Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise AuthenticationFailed(f"Failed to exchange code for tokens: {response.text}")
        
        tokens = response.json()
        print(f"✅ [OAUTH] Token exchange successful! Received keys: {list(tokens.keys())}")
        
        # The response contains:
        # - access_token: for Google API calls
        # - refresh_token: to refresh the access token (only on first auth)
        # - id_token: JWT with user info
        # - expires_in: token expiration time
        
        return tokens
        
    except requests.RequestException as e:
        print(f"❌ [OAUTH] Network error during token exchange: {e}")
        logger.error(f"Network error during token exchange: {e}")
        raise AuthenticationFailed(f"Network error: {e}")
    except Exception as e:
        print(f"❌ [OAUTH] Unexpected error during token exchange: {e}")
        print(f"❌ [OAUTH] Error type: {type(e).__name__}")
        import traceback
        print(f"❌ [OAUTH] Full traceback:\n{traceback.format_exc()}")
        logger.error(f"Unexpected error during token exchange: {e}")
        raise AuthenticationFailed(f"Token exchange failed: {e}")

def get_user_info_from_id_token(id_token):
    """
    Extract user information from the ID token (JWT)
    This is simpler than making additional API calls
    """
    print("🔍 [OAUTH] Starting get_user_info_from_id_token...")
    try:
        print("🔍 [OAUTH] Importing Google OAuth modules...")
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        print("✅ [OAUTH] Google OAuth modules imported successfully")
        
        print("🔍 [OAUTH] Verifying ID token...")
        # Verify and decode the ID token
        id_info = google_id_token.verify_oauth2_token(
            id_token, 
            google_requests.Request(), 
            settings.GOOGLE_OAUTH_CLIENT_ID
        )
        print("✅ [OAUTH] ID token verified successfully")
        print("✅ [OAUTH] ID token verified successfully")
        
        print("🔍 [OAUTH] Extracting user data from ID token...")
        # Extract user data from the ID token
        user_data = {
            'google_id': id_info['sub'],
            'email': id_info['email'],
            'email_verified': id_info.get('email_verified', False),
            'first_name': id_info.get('given_name', ''),
            'last_name': id_info.get('family_name', ''),
            'name': id_info.get('name', ''),
            'picture': id_info.get('picture', ''),
        }
        
        print(f"✅ [OAUTH] User data extracted for: {user_data.get('email', 'unknown')}")
        return user_data
        
    except Exception as e:
        print(f"❌ [OAUTH] Failed to decode ID token: {e}")
        print(f"❌ [OAUTH] Error type: {type(e).__name__}")
        import traceback
        print(f"❌ [OAUTH] Full traceback:\n{traceback.format_exc()}")
        logger.error(f"Failed to decode ID token: {e}")
        raise AuthenticationFailed(f"Invalid ID token: {e}")

def refresh_access_token(refresh_token):
    """
    Refresh the access token using refresh token
    Similar to: const { credentials } = await user.refreshAccessToken();
    """
    try:
        refresh_url = 'https://oauth2.googleapis.com/token'
        
        data = {
            'refresh_token': refresh_token,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(refresh_url, data=data)
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise AuthenticationFailed(f"Failed to refresh token: {response.text}")
        
        credentials = response.json()
        logger.info("Successfully refreshed access token")
        
        return credentials
        
    except requests.RequestException as e:
        logger.error(f"Network error during token refresh: {e}")
        raise AuthenticationFailed(f"Network error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise AuthenticationFailed(f"Token refresh failed: {e}")
