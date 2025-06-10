# HuesApply API Documentation

This document provides comprehensive documentation for all API endpoints in the HuesApply platform, including authentication, user management, and opportunities.

## Base URL

All API endpoints should be prefixed with the base URL:

- Production: `https://ha-backend-pq2f.vercel.app`
- Development: `http://localhost:8000`

For example, to access the Google client ID endpoint in production:
```
https://ha-backend-pq2f.vercel.app/api/auth/google-client-id/
```

## Table of Contents

1. [Authentication APIs](#authentication-apis)
   - [Google Sign-In](#google-sign-in)
   - [User Registration](#user-registration)
   - [Sign Out](#sign-out)
2. [User Management APIs](#user-management-apis)
   - [User Roles](#user-roles)
3. [Opportunities APIs](#opportunities-apis)
   - [Listing Opportunities](#listing-opportunities)
   - [Opportunity Details](#opportunity-details)
   - [Recommended Opportunities](#recommended-opportunities)
   - [Tracking](#tracking)

## Authentication APIs

### Google Sign-In

#### Get Google Client ID

Used by frontend to retrieve the Google OAuth Client ID.

**Endpoint**: `GET /api/auth/google-client-id/`  
**Authorization**: None required  
#### Get Google Client ID

Used by frontend to retrieve the Google OAuth Client ID.

**Endpoint**: `GET /api/auth/google-client-id/`  
**Authorization**: None required  
**Response**:
```json
{
  "client_id": "YOUR_GOOGLE_CLIENT_ID"
}
```

#### OAuth 2.0 Authorization Code Flow - Main Endpoint

**Primary OAuth Endpoint**: Exchange an authorization code for JWT tokens and user data.

**Endpoint**: `POST /api/auth/google/callback/`  
**Authorization**: None required  
**Request Body**:
```json
{
  "code": "GOOGLE_AUTHORIZATION_CODE"
}
```

**Response (Success - 200 OK)**:
```json
{
  "access_token": "JWT_ACCESS_TOKEN",
  "refresh_token": "JWT_REFRESH_TOKEN",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "country": "",
    "is_email_verified": true,
    "date_joined": "2024-01-15T10:30:00Z",
    "role": "Applicant",
    "profile": {
      "name": "John Doe",
      "email": "user@example.com",
      "profile_picture": "",
      "phone_number": "",
      "country": "",
      "goal": ""
    },
    "is_new_user": false,
    "google_data": {
      "name": "John Doe",
      "picture": "https://..."
    }
  }
}
```

**Response (Error - 400/401)**:
```json
{
  "error": "Error message"
}
```

---

### Legacy OAuth Endpoints (Deprecated)

The following endpoints are maintained for backward compatibility but should not be used in new implementations:

#### OAuth 2.0 Flow - Start (Legacy)

**Endpoint**: `GET /api/auth/google/start/`  
**Authorization**: None required  
**Response**:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=..."
}
```

#### OAuth 2.0 Flow - Redirect Callback (Legacy)

**Endpoint**: `GET /api/auth/google/redirect/`  
**Authorization**: None required  
**Query Parameters**:
- `code`: The authorization code from Google
- `state`: The state parameter for CSRF prevention

**Response**: Redirects to the frontend with tokens and user data as query parameters

#### OAuth 2.0 Flow - Code Exchange API (Legacy)

**Endpoint**: `POST /api/auth/google/`  
**Authorization**: None required  
**Request Body**:
```json
{
  "code": "GOOGLE_AUTHORIZATION_CODE"
}
```

**Response (Success - 200 OK)**:
```json
{
  "access_token": "JWT_ACCESS_TOKEN",
  "refresh_token": "JWT_REFRESH_TOKEN",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "Applicant",
    "is_new_user": false,
    "google_data": {
      "name": "John Doe",
      "picture": "https://..."
    }
  }
}
```

**Response (Error - 400/403)**:
```json
{
  "error": "Error message"
}
```

### User Registration

Register a new user with email and password.

**Endpoint**: `POST /api/register/`  
**Authorization**: None required  
**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "role": "applicant" // or "employer"
}
```

**Response (Success - 201 Created)**:
```json
{
  "access_token": "JWT_ACCESS_TOKEN",
  "refresh_token": "JWT_REFRESH_TOKEN",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "Applicant",
    "is_new_user": true
  }
}
```

**Response (Error - 400)**:
```json
{
  "email": ["This email is already in use."],
  "password": ["This password is too short."]
}
```

### Sign Out

Blacklist a JWT refresh token when the user signs out.

**Endpoint**: `POST /api/auth/sign-out/`  
**Authorization**: JWT Bearer token required  
**Request Body**:
```json
{
  "refresh_token": "JWT_REFRESH_TOKEN"
}
```

**Response (Success - 200 OK)**:
```json
{
  "success": "User logged out successfully"
}
```

**Response (Error - 400)**:
```json
{
  "error": "Refresh token is required"
}
```

## User Management APIs

### User Roles

#### Get User Role

Get the current user's role information.

**Endpoint**: `GET /api/role/`  
**Authorization**: JWT Bearer token required  
**Response (Success - 200 OK)**:
```json
{
  "role": "Applicant",
  "is_applicant": true,
  "is_employer": false,
  "is_admin": false
}
```

#### Update User Role

Change the user's role.

**Endpoint**: `POST /api/role/`  
**Authorization**: JWT Bearer token required  
**Request Body**:
```json
{
  "role": "employer" // or "applicant"
}
```

**Response (Success - 200 OK)**:
```json
{
  "message": "Role updated to Employer"
}
```

**Response (Error - 400)**:
```json
{
  "error": "Invalid role specified"
}
```

## Opportunities APIs

### Listing Opportunities

Get a list of opportunities with filtering, search, and pagination.

**Endpoint**: `GET /api/opportunities/`  
**Authorization**: None required (public endpoint)  
**Query Parameters**:
- `page`: Page number (default 1)
- `page_size`: Number of items per page (default 10, max 100)
- `search`: Full-text search query
- `type`: Filter by opportunity type
- `location`: Filter by location
- `is_remote`: Filter by remote status (true/false)
- `category__slug`: Filter by category slug
- `tags__slug`: Filter by tag slug
- `deadline`: Filter by deadline date
- `show_expired`: Include expired opportunities (default false)
- `ordering`: Sort field, prefix with '-' for descending (e.g. '-deadline', 'title')

**Response**:
```json
{
  "count": 100,
  "next": "http://example.com/api/opportunities/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Software Engineer",
      "organization": "Tech Company",
      "description": "Job description...",
      "type": "job",
      "location": "New York",
      "is_remote": true,
      "deadline": "2025-07-01",
      "category": {
        "name": "Engineering",
        "slug": "engineering"
      },
      "tags": [
        {
          "name": "Python",
          "slug": "python"
        }
      ],
      "posted_by": "employer@example.com",
      "created_at": "2025-06-01T12:00:00Z"
    }
  ]
}
```

### Opportunity Details

Get details of a specific opportunity.

**Endpoint**: `GET /api/opportunities/{id}/`  
**Authorization**: None required (public endpoint)  
**Response**: Same as individual opportunity object above

### Recommended Opportunities

Get personalized opportunity recommendations based on user profile.

**Endpoint**: `GET /api/opportunities/recommended/`  
**Authorization**: JWT Bearer token required  
**Query Parameters**:
- `page`: Page number (default 1)
- `page_size`: Number of items per page (default 10, max 100)
- `type`: Filter by opportunity type
- `location`: Filter by location
- `category`: Filter by category
- `tags`: Filter by tags (can be multiple)
- `skills`: Filter by skills (can be multiple)
- `deadline_after`: Filter by deadline after date
- `deadline_before`: Filter by deadline before date
- `ordering`: Sort field, prefix with '-' for descending (e.g. '-score', 'deadline')

**Response**:
```json
{
  "count": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "opportunity": {
        "id": 1,
        "title": "Software Engineer",
        // ... same as regular opportunity
      },
      "score": 0.85,
      "match_reasons": ["Skills match", "Location match"]
    }
  ]
}
```

### Tracking

#### Track View

Track that a user viewed an opportunity.

**Endpoint**: `POST /api/opportunities/{id}/track_view/`  
**Authorization**: None required  
**Response**:
```json
{
  "status": "view tracked",
  "view_count": 42
}
```

#### Track Application

Track that a user applied to an opportunity.

**Endpoint**: `POST /api/opportunities/{id}/track_application/`  
**Authorization**: JWT Bearer token required  
**Response**:
```json
{
  "status": "application tracked",
  "application_count": 15
}
```

## Frontend Integration Guide

### Authentication Flow with OAuth 2.0 Redirect

#### 1. Implementing Google Sign-In with OAuth Redirect Flow

```javascript
// Get the authorization URL from your backend and redirect to Google
function initiateGoogleSignIn() {
  fetch('https://ha-backend-pq2f.vercel.app/api/auth/google/start/')
    .then(res => res.json())
    .then(data => {
      // Store state in localStorage for security validation after redirect
      const authUrl = new URL(data.auth_url);
      const params = new URLSearchParams(authUrl.search);
      const state = params.get('state');
      localStorage.setItem('oauth_state', state);
      
      // Redirect to Google's OAuth page
      window.location.href = data.auth_url;
    })
    .catch(error => {
      console.error('Error starting OAuth flow:', error);
    });
}
```

#### 2. Handling the OAuth Callback

Create a component to handle the OAuth callback:

```javascript
// Implement in your callback component (e.g., GoogleAuthCallback.js)
function handleOAuthCallback() {
  // Get URL parameters from the callback
  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get('access_token');
  const refreshToken = urlParams.get('refresh_token');
  const userDataString = urlParams.get('user_data');
  const error = urlParams.get('error');
  
  if (error) {
    console.error('Authentication error:', error);
    // Show error to user and redirect to login
    window.location.href = '/login?error=' + encodeURIComponent(error);
    return;
  }
  
  if (accessToken && refreshToken) {
    // Authentication successful!
    // Store tokens securely
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
    
    // Parse and store user data
    if (userDataString) {
      try {
        const userData = JSON.parse(userDataString);
        localStorage.setItem('user', userDataString);
        
        // Handle new user if needed
        if (userData.is_new_user) {
          window.location.href = '/onboarding';
          return;
        }
      } catch (e) {
        console.error('Error parsing user data:', e);
      }
    }
    
    // Redirect to dashboard
    window.location.href = '/dashboard';
  } else {
    // No tokens in URL - try the code exchange API instead
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const storedState = localStorage.getItem('oauth_state');
    
    // Validate state to prevent CSRF attacks
    if (!state || !storedState || state !== storedState) {
      console.error('Invalid state parameter. Possible CSRF attack.');
      window.location.href = '/login?error=invalid_state';
      return;
    }
    
    // Clear stored state
    localStorage.removeItem('oauth_state');
    
    if (code) {
      // Exchange the code for tokens via the direct API
      fetch('https://ha-backend-pq2f.vercel.app/api/auth/google/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code })
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          console.error('Authentication error:', data.error);
          window.location.href = '/login?error=' + encodeURIComponent(data.error);
          return;
        }
        
        // Store tokens securely
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('refreshToken', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to appropriate page
        if (data.user.is_new_user) {
          window.location.href = '/onboarding';
        } else {
          window.location.href = '/dashboard';
        }
      })
      .catch(error => {
        console.error('Authentication error:', error);
        window.location.href = '/login?error=server_error';
      });
    } else {
      console.error('No authorization code or tokens provided');
      window.location.href = '/login?error=no_code';
    }
  }
}
```

#### 3. Google Sign-In Button Component

```jsx
// React component for Google Sign-In button
function GoogleSignInButton() {
  const handleSignInClick = () => {
    // Start the OAuth flow
    fetch('https://ha-backend-pq2f.vercel.app/api/auth/google/start/')
      .then(res => res.json())
      .then(data => {
        // Store state in localStorage for security validation after redirect
        const authUrl = new URL(data.auth_url);
        const params = new URLSearchParams(authUrl.search);
        const state = params.get('state');
        localStorage.setItem('oauth_state', state);
        
        // Redirect to Google's OAuth page
        window.location.href = data.auth_url;
      });
  };

  return (
    <button 
      className="google-sign-in-button" 
      onClick={handleSignInClick}
    >
      <img 
        src="/google-icon.svg" 
        alt="Google logo" 
      />
      Sign in with Google
    </button>
  );
}
```

#### 4. Making Authenticated Requests

```javascript
function fetchUserData() {
  fetch('https://ha-backend-pq2f.vercel.app/api/role/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
    }
  })
  .then(res => res.json())
  .then(data => {
    // Update UI with user role information
    console.log('User role:', data.role);
  });
}
```

#### 5. Sign Out

```javascript
function signOut() {
  const refreshToken = localStorage.getItem('refreshToken');
  
  fetch('https://ha-backend-pq2f.vercel.app/api/auth/sign-out/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
    },
    body: JSON.stringify({
      refresh_token: refreshToken
    })
  })
  .then(() => {
    // Clear local storage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    
    // Redirect to home or login
    window.location.href = '/';
  });
}
```

### Working with Opportunities

#### 1. Fetching Opportunities List

```javascript
function fetchOpportunities(page = 1) {
  // Build query string with filters
  const filters = {
    page,
    page_size: 10,
    search: document.getElementById('search').value,
    type: document.getElementById('typeFilter').value,
    location: document.getElementById('locationFilter').value,
    ordering: document.getElementById('sorting').value
  };
  
  const queryString = Object.entries(filters)
    .filter(([_, value]) => value) // Remove empty values
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
    .join('&');
  
  fetch(`https://ha-backend-pq2f.vercel.app/api/opportunities/?${queryString}`)
    .then(res => res.json())
    .then(data => {
      // Render opportunities list
      renderOpportunities(data.results);
      
      // Update pagination
      updatePagination(data.count, data.next, data.previous);
    });
}
```

#### 2. Getting Recommended Opportunities

```javascript
function fetchRecommendations() {
  fetch('https://ha-backend-pq2f.vercel.app/api/opportunities/recommended/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
    }
  })
  .then(res => res.json())
  .then(data => {
    // Render recommended opportunities
    renderRecommendations(data.results);
  });
}
```

#### 3. Tracking User Interactions

```javascript
function trackOpportunityView(opportunityId) {
  fetch(`https://ha-backend-pq2f.vercel.app/api/opportunities/${opportunityId}/track_view/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
}

function trackOpportunityApplication(opportunityId) {
  fetch(`https://ha-backend-pq2f.vercel.app/api/opportunities/${opportunityId}/track_application/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
    }
  });
}
```

## Security Considerations

1. Always verify the Google token with Google's servers (done on backend)
2. Check that the email is verified by Google (done on backend)
3. Store JWT tokens securely (preferably in HttpOnly cookies for production)
4. Use HTTPS in production
5. Implement token refresh mechanism for long user sessions
6. Set appropriate CORS headers for your frontend domain
7. Validate all user input on both frontend and backend
