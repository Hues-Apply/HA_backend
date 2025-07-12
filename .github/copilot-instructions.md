# HuesApply Backend - AI Coding Agent Instructions

## Project Overview
Django REST API backend for HuesApply - an opportunity matching platform connecting users to jobs, scholarships, grants, and fellowships. Core feature is an AI-powered recommendation engine that matches users to opportunities based on their skills, education, location, and preferences.

## Essential Architecture

### Core Apps & Responsibilities
- **`users/`**: Custom user auth system with Google OAuth, role-based permissions (`Applicants`/`Employers`), multi-profile document parsing
- **`opportunities/`**: Opportunity CRUD, advanced search, recommendation engine (`OpportunityMatcher` class)
- **`config/`**: Django settings with environment-based configuration, JWT auth, CORS setup
- **`core/`**: Shared utilities (currently minimal)

### Key Data Models
- **CustomUser**: Email-based auth with role management (`set_as_applicant()`, `set_as_employer()`)
- **UserProfile**: Stores Google OAuth tokens, profile pictures, parsed CV data
- **Opportunity**: Core model with `eligibility_criteria` JSON field, M2M tags, full-text search
- **Document/ParsedProfile**: CV parsing workflow with processing states

### Authentication Flow
1. Google OAuth via `users/google_oauth.py` (ID token verification)
2. JWT tokens via `django-rest-framework-simplejwt` 
3. Fallback simple tokens for cryptography issues
4. Role assignment on first login (`user.set_as_applicant()`)

## Critical Developer Workflows

### Testing
```bash
# Use Django test runner, NOT pytest directly
python manage.py test opportunities.tests.test_matching
python manage.py test users.tests

# For specific test classes
python manage.py test opportunities.tests.test_matching.MatchingAlgorithmTests
```

### Sample Data Generation
```bash
# Generate test opportunities (uses Faker)
python manage.py generate_sample_data --count 1000

# Setup user roles and permissions
python manage.py setup_roles
```

### Environment Setup
- **Required env vars**: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- **Database**: PostgreSQL (uses `dj-database-url` for parsing)
- **Cache**: Redis integration for recommendation caching

### API Testing
```bash
# Test recommendations endpoint (requires auth)
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/opportunities/recommended/?ordering=-score&page_size=10"
```

## Project-Specific Patterns

### Recommendation Engine (`opportunities/matching.py`)
- **OpportunityMatcher**: Weighted scoring algorithm (skills 40%, location 20%, education 25%, preferences 15%)
- **Caching**: User recommendations cached for 30 minutes, cache keys include filters
- **Scoring**: Returns 0-100 scores with detailed breakdown in `reasons` field
- **Mock Testing**: Use `MockUserProfile` class for unit tests

### API Response Patterns
```python
# Standard error format
{"error": "descriptive message", "details": {...}}

# Paginated responses (using DRF PageNumberPagination)
{"count": 100, "next": "...", "previous": "...", "results": [...]}

# Recommendation format
{"opportunity": {...}, "score": 85, "reasons": {"skills_match": 90, ...}}
```

### Google OAuth Implementation
- **ID Token Flow**: Direct credential verification (no code exchange for web)
- **Token Storage**: Access/refresh tokens stored in `UserProfile`
- **Error Handling**: Graceful fallback when google-auth unavailable
- **Debug Logging**: Extensive print statements for OAuth troubleshooting

### File Upload Patterns
- **Document Upload**: UUID-based paths, validation for size (10MB) and format (PDF/DOC/DOCX)
- **Profile Pictures**: Size/format validation via custom validators
- **Processing States**: `pending` → `processing` → `completed`/`failed`

## Integration Points

### Frontend Communication
- **CORS**: Configured for `localhost:5173` (React dev server)
- **Response Format**: Consistent JSON with snake_case fields
- **Auth Headers**: `Authorization: Bearer <jwt_token>`

### External Services
- **Google OAuth**: Custom implementation in `users/google_oauth.py`
- **Vercel Deployment**: Uses `sync_repos.sh` for org→personal fork sync
- **Static Files**: WhiteNoise for production static serving

## Common Gotchas

### Testing Django Models
```python
# Always use Django TestCase for model tests
from django.test import TestCase
# NOT: from unittest import TestCase

# For user auth in tests
user = CustomUser.objects.create_user(email="test@example.com")
user.set_as_applicant()  # Don't forget role assignment
```

### Opportunity Filtering
```python
# Use proper field lookups for JSON fields
queryset.filter(eligibility_criteria__education_level='bachelors')

# For M2M tags filtering
queryset.filter(tags__slug__in=['python', 'django'])
```

### Cache Key Generation
```python
# Include user context in cache keys
cache_key = f'user_recommendations_{user.id}_{filters_hash}'
```

### Error Handling Patterns
```python
# Standard view error handling
try:
    # logic here
    return Response(data, status=status.HTTP_200_OK)
except ValidationError as e:
    return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
except Exception as e:
    return Response({"error": f"Operation failed: {str(e)}"}, 
                   status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

## Key Files to Understand
- `opportunities/matching.py` - Core recommendation algorithm
- `users/google_oauth.py` - Custom OAuth implementation  
- `opportunities/api/views.py` - API patterns and caching
- `users/models.py` - Custom user and profile models
- `config/settings.py` - Environment configuration patterns


## Additional Instructions
- Always keep the codebase DRY (Don't Repeat Yourself).
- Keep the code modular and maintainable.
- Keep the implementation simple and straightforward.
- Don't write tests unless explicitly requested.
- Use Django's built-in testing framework for all tests.
- Make the implementation efficient and optimized for performance.
- Ensure that all API endpoints are well-documented and follow RESTful principles.
- Don't write code that I didn't explicitly ask for, even if it is necessary to complete the task at hand.
