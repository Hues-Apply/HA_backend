# HuesApply Backend Setup Guide

This guide explains how to set up the HuesApply backend with the latest security and architectural improvements.

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis (for caching)
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HA_backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

## Environment Configuration

### Required Environment Variables

Copy `env.example` to `.env` and configure the following variables:

#### Critical Security Variables
```bash
DJANGO_SECRET_KEY=your-long-random-secret-key-here
DEBUG=False  # Set to True only for development
```

#### Database Configuration
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/huesapply_db
```

#### Google OAuth (Required)
```bash
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

#### Frontend URL
```bash
FRONTEND_URL=http://localhost:5173
```

## Database Setup

1. **Create PostgreSQL database**
   ```sql
   CREATE DATABASE huesapply_db;
   CREATE USER huesapply_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE huesapply_db TO huesapply_user;
   ```

2. **Run migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

## Security Checklist

### ✅ Completed Security Fixes

1. **Hardcoded Secret Key**: Moved to environment variable
2. **Security Headers**: Added comprehensive security headers
3. **Input Validation**: Implemented input sanitization
4. **Error Handling**: Standardized error responses
5. **Logging**: Replaced print statements with proper logging
6. **Data Types**: Fixed model field types for better validation
7. **Database Indexes**: Added performance indexes
8. **Constants**: Centralized configuration values

### 🔒 Security Best Practices

1. **Never commit `.env` files** - They contain sensitive information
2. **Use strong passwords** for database and admin accounts
3. **Keep dependencies updated** - Run `pip audit` regularly
4. **Monitor logs** for suspicious activity
5. **Use HTTPS in production** - SSL certificates are required
6. **Regular backups** - Set up automated database backups

## Development Setup

1. **Enable debug mode** (development only)
   ```bash
   DEBUG=True
   ```

2. **Run development server**
   ```bash
   python manage.py runserver
   ```

3. **Run tests**
   ```bash
   python manage.py test
   ```

## Production Deployment

### Security Requirements

1. **Environment Variables**: All secrets must be in environment variables
2. **HTTPS**: SSL certificates required
3. **Database**: Use managed PostgreSQL service
4. **Caching**: Configure Redis for caching
5. **Monitoring**: Set up logging and monitoring

### Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure Redis for caching
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Configure rate limiting
- [ ] Set up error tracking (Sentry)

## API Documentation

### Standardized Response Format

All API endpoints now return standardized responses:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful",
  "errors": []
}
```

**Error Response:**
```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "errors": ["Detailed error messages"]
}
```

### Authentication

The API uses JWT tokens for authentication:

1. **Login**: POST `/api/auth/google/` or `/api/auth/google/callback/`
2. **Token Refresh**: POST `/api/auth/refresh/`
3. **Logout**: POST `/api/auth/logout/`

Include the JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Architecture Improvements

### Service Layer

Business logic has been moved to service classes:
- `OpportunityService`: Handles opportunity operations
- `UserService`: Handles user operations
- `MatchingService`: Handles recommendation algorithms

### Constants Management

All hardcoded values are now in `config/constants.py`:
- File upload limits
- Matching algorithm weights
- Cache timeouts
- Error messages

### Error Handling

Standardized error handling with:
- Consistent error responses
- Proper HTTP status codes
- Input validation
- Exception logging

## Monitoring and Logging

### Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General information about application flow
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for actual problems
- `CRITICAL`: Critical errors that require immediate attention

### Log Format

Logs include:
- Timestamp
- Log level
- Module name
- User information (when available)
- Request details
- Error stack traces

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL in .env
   - Ensure PostgreSQL is running
   - Verify database permissions

2. **Google OAuth Errors**
   - Verify GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET
   - Check redirect URI configuration
   - Ensure Google OAuth is enabled in Google Console

3. **Migration Errors**
   - Run `python manage.py showmigrations` to check status
   - Use `python manage.py migrate --fake-initial` if needed
   - Check for conflicting migrations

4. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility

### Getting Help

1. Check the logs for detailed error messages
2. Review the Django documentation
3. Check the API response format for error details
4. Contact the development team with specific error messages

## Contributing

When contributing to the codebase:

1. **Follow the coding standards** - Use the established patterns
2. **Add tests** - Ensure new features are tested
3. **Update documentation** - Keep this guide current
4. **Use the service layer** - Don't put business logic in views
5. **Follow security practices** - Never commit secrets
6. **Use constants** - Don't hardcode values

## Support

For technical support or questions:
- Check the logs for error details
- Review the API documentation
- Contact the development team
