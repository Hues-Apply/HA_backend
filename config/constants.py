"""
Configuration constants for HuesApply backend.
This file centralizes all hardcoded values and configuration constants.
"""

# File upload limits
MAX_FILE_SIZE_KB = 500
MAX_IMAGE_SIZE_KB = 500
ALLOWED_FILE_TYPES = ['pdf', 'doc', 'docx', 'txt']
ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png', 'gif']

# Matching algorithm weights
MATCHING_WEIGHTS = {
    'skills_match': 0.4,
    'location_match': 0.2,
    'education_match': 0.25,
    'preferences_match': 0.15,
    'experience_match': 0.15,
}

# Default scores
DEFAULT_KEYWORD_SCORE = 0.5
DEFAULT_LOCATION_SCORE = 0.3
DEFAULT_EDUCATION_SCORE = 0.4

# Cache settings
CACHE_TIMEOUT = 3600  # 1 hour
RECOMMENDATION_CACHE_TIMEOUT = 1800  # 30 minutes
USER_PROFILE_CACHE_TIMEOUT = 7200  # 2 hours

# Pagination settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Search settings
MAX_SEARCH_RESULTS = 1000
SEARCH_MIN_SCORE = 0.1

# OAuth settings
GOOGLE_OAUTH_CLOCK_SKEW_SECONDS = 10  # Reduced from 60 for better security

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600  # 1 hour

# Email verification
EMAIL_VERIFICATION_TIMEOUT = 86400  # 24 hours

# Job crawling settings
MAX_JOBS_PER_BATCH = 1000
CRAWLING_DELAY_SECONDS = 1

# Scholarship settings
SCHOLARSHIP_DEADLINE_WARNING_DAYS = 30

# User roles
USER_ROLES = {
    'applicant': 'Applicant',
    'employer': 'Employer',
    'admin': 'Admin',
}

# Opportunity types
OPPORTUNITY_TYPES = {
    'job': 'Job',
    'scholarship': 'Scholarship',
    'grant': 'Grant',
    'internship': 'Internship',
    'fellowship': 'Fellowship',
}

# Experience levels
EXPERIENCE_LEVELS = {
    'entry': 'Entry Level',
    'mid': 'Mid Level',
    'senior': 'Senior Level',
    'executive': 'Executive Level',
}

# Job types
JOB_TYPES = {
    'full-time': 'Full Time',
    'part-time': 'Part Time',
    'contract': 'Contract',
    'internship': 'Internship',
    'freelance': 'Freelance',
    'temporary': 'Temporary',
}

# Application statuses
APPLICATION_STATUSES = {
    'applied': 'Applied',
    'interviewing': 'Interviewing',
    'offered': 'Offered',
    'rejected': 'Rejected',
    'withdrawn': 'Withdrawn',
}

# Currency codes
SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'INR']

# Location settings
DEFAULT_COUNTRY = 'US'
DEFAULT_TIMEZONE = 'UTC'

# API settings
API_VERSION = 'v1'
API_RESPONSE_FORMAT = {
    'success': True,
    'data': None,
    'message': '',
    'errors': [],
}

# Error messages
ERROR_MESSAGES = {
    'invalid_credentials': 'Invalid credentials provided',
    'permission_denied': 'You do not have permission to perform this action',
    'resource_not_found': 'The requested resource was not found',
    'validation_error': 'Validation error occurred',
    'server_error': 'An internal server error occurred',
    'rate_limit_exceeded': 'Rate limit exceeded. Please try again later',
    'file_too_large': f'File size must not exceed {MAX_FILE_SIZE_KB} KB',
    'invalid_file_type': 'Invalid file type provided',
    'oauth_unavailable': 'OAuth service is currently unavailable',
    'email_not_verified': 'Email address is not verified',
}

# Success messages
SUCCESS_MESSAGES = {
    'user_created': 'User created successfully',
    'user_updated': 'User updated successfully',
    'user_deleted': 'User deleted successfully',
    'opportunity_created': 'Opportunity created successfully',
    'opportunity_updated': 'Opportunity updated successfully',
    'application_submitted': 'Application submitted successfully',
    'profile_updated': 'Profile updated successfully',
    'password_changed': 'Password changed successfully',
    'email_verified': 'Email verified successfully',
    'oauth_success': 'OAuth authentication successful',
}
