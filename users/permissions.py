from rest_framework import permissions
from django.contrib.auth.models import Group
from jobs.models import Job, UserJob
from scholarships.models import Scholarship, UserScholarship
from opportunities.models import Opportunity


class IsApplicant(permissions.BasePermission):
    """
    Permission to check if user is an applicant.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_applicant()


class IsEmployer(permissions.BasePermission):
    """
    Permission to check if user is an employer.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_employer()


class IsAdministrator(permissions.BasePermission):
    """
    Permission to check if user is an administrator.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class IsApplicantOrEmployer(permissions.BasePermission):
    """
    Permission to check if user is either an applicant or employer.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_applicant() or request.user.is_employer()
        )


class IsEmployerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is either an employer or administrator.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_employer() or request.user.is_superuser
        )


class IsApplicantOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is either an applicant or administrator.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_applicant() or request.user.is_superuser
        )


# Job-specific permissions
class JobPermissions(permissions.BasePermission):
    """
    Comprehensive permissions for Job operations.
    """
    def has_permission(self, request, view):
        # Allow public access for viewing jobs
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require authentication for other operations
        if not request.user.is_authenticated:
            return False

        # Only employers and admins can create jobs
        if view.action == 'create':
            return request.user.is_employer() or request.user.is_superuser

        # Only employers and admins can update/delete jobs
        if view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_employer() or request.user.is_superuser

        # Only applicants can apply to jobs
        if view.action == 'apply':
            return request.user.is_applicant()

        # Only authenticated users can view their applications
        if view.action == 'applications':
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Allow public access for viewing
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the job creator (employer) or admin can edit/delete
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return (
                (hasattr(obj, 'created_by') and obj.created_by == request.user) or
                request.user.is_superuser
            )

        return False


# Scholarship-specific permissions
class ScholarshipPermissions(permissions.BasePermission):
    """
    Comprehensive permissions for Scholarship operations.
    """
    def has_permission(self, request, view):
        # Allow public access for viewing scholarships
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require authentication for other operations
        if not request.user.is_authenticated:
            return False

        # Only admins can create/edit/delete scholarships (since they're typically scraped)
        if view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user.is_superuser

        # Only applicants can apply to scholarships
        if view.action == 'apply':
            return request.user.is_applicant()

        # Only authenticated users can view their applications
        if view.action == 'applications':
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Allow public access for viewing
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only admins can edit/delete scholarships
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return request.user.is_superuser

        return False


# Opportunity-specific permissions
class OpportunityPermissions(permissions.BasePermission):
    """
    Comprehensive permissions for Opportunity operations.
    """
    def has_permission(self, request, view):
        # Allow public access for viewing opportunities
        if request.method in permissions.SAFE_METHODS:
            return True

        # Require authentication for other operations
        if not request.user.is_authenticated:
            return False

        # Only employers and admins can create opportunities
        if view.action == 'create':
            return request.user.is_employer() or request.user.is_superuser

        # Only employers and admins can update/delete opportunities
        if view.action in ['update', 'partial_update', 'destroy']:
            return request.user.is_employer() or request.user.is_superuser

        # Only applicants can apply to opportunities
        if view.action == 'apply':
            return request.user.is_applicant()

        # Only authenticated users can view their applications
        if view.action == 'applications':
            return True

        # Bulk operations require employer or admin permissions
        if view.action == 'bulk_create':
            return request.user.is_employer() or request.user.is_superuser

        return False

    def has_object_permission(self, request, view, obj):
        # Allow public access for viewing
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the opportunity creator (employer) or admin can edit/delete
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return (
                (hasattr(obj, 'created_by') and obj.created_by == request.user) or
                request.user.is_superuser
            )

        return False


# User application permissions
class UserApplicationPermissions(permissions.BasePermission):
    """
    Permissions for user application tracking (UserJob, UserScholarship).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own applications
        return obj.user == request.user


# Profile permissions
class ProfilePermissions(permissions.BasePermission):
    """
    Permissions for user profile operations.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own profile
        return obj.user == request.user


# Document permissions
class DocumentPermissions(permissions.BasePermission):
    """
    Permissions for document uploads and management.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own documents
        return obj.user == request.user


# Utility permission classes for common patterns
class ReadOnlyOrAuthenticated(permissions.BasePermission):
    """
    Allow read access to everyone, write access to authenticated users.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated


class ReadOnlyOrEmployerAdmin(permissions.BasePermission):
    """
    Allow read access to everyone, write access to employers and admins.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_employer() or request.user.is_superuser
        )


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Allow read access to everyone, write access to admins only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.is_superuser


# Permission mixins for easy reuse
class RoleBasedPermissionMixin:
    """
    Mixin to provide role-based permissions for ViewSets.
    """
    def get_permissions(self):
        """
        Return permissions based on action and user role.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Default to employer/admin for CRUD operations
            permission_classes = [IsEmployerOrAdmin]
        elif self.action in ['apply']:
            # Only applicants can apply
            permission_classes = [IsApplicant]
        elif self.action in ['applications']:
            # Authenticated users can view their applications
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Public read access
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]


class JobPermissionMixin(RoleBasedPermissionMixin):
    """
    Specific permission mixin for Job ViewSets.
    """
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsEmployerOrAdmin]
        elif self.action in ['apply']:
            permission_classes = [IsApplicant]
        elif self.action in ['applications']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]


class ScholarshipPermissionMixin(RoleBasedPermissionMixin):
    """
    Specific permission mixin for Scholarship ViewSets.
    """
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admins can manage scholarships
            permission_classes = [IsAdministrator]
        elif self.action in ['apply']:
            permission_classes = [IsApplicant]
        elif self.action in ['applications']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]
