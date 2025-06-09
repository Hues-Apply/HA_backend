# HuesApply API Tests

This folder contains comprehensive tests for all the API endpoints in the HuesApply platform.

## Test Structure

The tests are organized based on the functional areas of the application:

1. **Authentication Tests** (`users/tests/test_auth_api.py`)
   - Google OAuth endpoints
   - User registration
   - Sign out functionality

2. **User Management Tests** (`users/tests/test_user_api.py`)
   - User role endpoints
   - User profile operations

3. **Opportunity Listing Tests** (`opportunities/tests/test_opportunities_api.py`)
   - Opportunity listing and filtering
   - Opportunity details

4. **Opportunity Tracking Tests** (`opportunities/tests/test_tracking_api.py`)
   - View tracking
   - Application tracking

5. **Recommendations Tests** (`opportunities/tests/test_recommendations_api.py`)
   - Personalized opportunity recommendations

6. **Applications Tests** (`applications/tests/test_applications_api.py`)
   - Application submission
   - Application status management

## Running the Tests

You can run all API tests with:

```bash
python run_api_tests.py
```

Or run specific test modules:

```bash
python run_api_tests.py users.tests.test_auth_api
```

## Test Coverage

These tests cover:

- Authentication and authorization
- Permission checks for different user roles
- Filtering and search functionality
- Data validation
- Response structure and status codes
- Error handling

## Test Utility Classes

The test utilities in `users/tests/test_utils.py` provide:

- `BaseAPITestCase`: A base test case with authentication helpers
- User role helpers (admin, applicant, employer)
- JWT token generation

## Adding New Tests

When adding new API endpoints, please add corresponding tests that cover:

1. Successful operations with valid data
2. Error cases with invalid data
3. Permission checks
4. Edge cases specific to the endpoint

## Test Data

The tests create their own isolated test data, including:
- Test users with different roles
- Sample opportunities
- Categories and tags
- Applications

This ensures tests are repeatable and don't depend on existing database state.
