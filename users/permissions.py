from rest_framework import permissions

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
