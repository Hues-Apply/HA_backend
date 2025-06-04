# User Role Management

This document explains how to use the role management system implemented in the HuesApply platform.

## Overview

The role management system uses Django's built-in Groups to manage user roles. There are three main roles:

1. **Applicants**: Users who apply for opportunities
2. **Employers**: Users who post job opportunities
3. **Administrators**: Users with full administrative rights

## Setting Up Roles

Run the following command to set up the initial roles and permissions:

```bash
python manage.py setup_roles
```

This will create the necessary groups and assign permissions.

## Working with Roles in Code

### Assigning Roles

```python
# Import the CustomUser model
from users.models import CustomUser

# Create a user and assign a role
user = CustomUser.objects.create_user(email="example@email.com", password="secure_password")
user.set_as_applicant()  # Set as applicant
# OR
user.set_as_employer()  # Set as employer

# You can also use generic methods
user.add_to_role('Applicants')
user.remove_from_role('Employers')
```

### Checking Roles

```python
# Check if a user has a specific role
if user.is_applicant():
    # Do something for applicants
elif user.is_employer():
    # Do something for employers
elif user.is_superuser:  # Django's built-in superuser check
    # Do something for administrators

# Get the user's role as a string
role = user.get_role()  # Returns "Applicant", "Employer", "Administrator", or "Unassigned"
```

### Using Permission Classes in Views

```python
from users.permissions import IsApplicant, IsEmployer, IsAdministrator
from rest_framework.views import APIView

class ApplicantOnlyView(APIView):
    permission_classes = [IsApplicant]
    # ...

class EmployerOnlyView(APIView):
    permission_classes = [IsEmployer]
    # ...

class AdminOnlyView(APIView):
    permission_classes = [IsAdministrator]
    # ...
```

## API Endpoints

### Get Current User's Role

```
GET /api/user/role/
```

Returns:
```json
{
    "role": "Applicant",
    "is_applicant": true,
    "is_employer": false,
    "is_admin": false
}
```

### Update User Role

```
POST /api/user/role/
```

Payload:
```json
{
    "role": "employer"  // or "applicant"
}
```

Returns:
```json
{
    "message": "Role updated to Employer"
}
```

## Templates

When registering a user, you can provide a role selection:

```html
<form method="post" action="{% url 'users:register' %}">
    {% csrf_token %}
    <!-- Other form fields -->
    <div class="form-group">
        <label>I am a:</label>
        <select name="role" required>
            <option value="applicant">Job Seeker</option>
            <option value="employer">Employer</option>
        </select>
    </div>
    <button type="submit">Register</button>
</form>
```
