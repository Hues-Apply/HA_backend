from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, CareerProfile, EducationProfile, ExperienceProfile

class CustomUserAdmin(UserAdmin):
    """Admin configuration for the CustomUser model."""
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_email_verified')
    list_filter = ('is_staff', 'is_active', 'is_email_verified')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified',
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email', 'phone_number', 'country')
    search_fields = ('name', 'email', 'phone_number', 'country')

class CareerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'industry', 'job_title')
    search_fields = ('user__email', 'industry', 'job_title')

class EducationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'degree', 'school', 'start_date', 'end_date')
    search_fields = ('user__email', 'degree', 'school')

class ExperienceProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title', 'company_name', 'location')
    search_fields = ('user__email', 'job_title', 'company_name')

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(CareerProfile, CareerProfileAdmin)
admin.site.register(EducationProfile, EducationProfileAdmin)
admin.site.register(ExperienceProfile, ExperienceProfileAdmin)
