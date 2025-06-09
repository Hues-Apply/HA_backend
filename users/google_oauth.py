"""
Google OAuth 2.0 functionality for HuesApply backend
"""
import os
import json
import requests
from django.conf import settings
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class GoogleOAuth:
    """Google OAuth 2.0 helper class"""
    
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://oauth2.googleapis.com/token'
    USER_INFO_URI = 'https://www.googleapis.com/oauth2/v3/userinfo'
    
    def __init__(self):
        self.client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
        
    def get_auth_url(self, state=None):
        """Generate the authorization URL for Google OAuth 2.0"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'offline',
            'prompt': 'consent',
        }
        
        if state:
            params['state'] = state
            
        return f"{self.AUTH_URI}?{urlencode(params)}"
        
    def exchange_code_for_token(self, code):
        """Exchange authorization code for token"""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(self.TOKEN_URI, data=data)
        
        if response.status_code != 200:
            logger.error(f"Failed to exchange code: {response.text}")
            return None
            
        return response.json()
        
    def get_user_info(self, access_token):
        """Get user info from Google with an access token"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URI, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            return None
            
        return response.json()
