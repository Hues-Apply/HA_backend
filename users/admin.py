from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, UserProfile, CareerProfile, EducationProfile, ExperienceProfile,
    Document, ParsedProfile, UserGoal
)

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

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'document_type', 'processing_status', 'uploaded_at')
    list_filter = ('document_type', 'processing_status', 'uploaded_at')
    search_fields = ('user__email', 'original_filename')
    readonly_fields = ('id', 'uploaded_at', 'processed_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


class ParsedProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'confidence_score', 'completion_percentage', 'parsed_at')
    list_filter = ('parsed_at', 'updated_at')
    search_fields = ('user__email', 'first_name', 'last_name')
    readonly_fields = ('completion_percentage', 'parsed_at', 'updated_at')
    
    fieldsets = (
        ('User', {'fields': ('user', 'document')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'linkedin', 'portfolio')
        }),
        ('Professional Summary', {'fields': ('summary',)}),
        ('Structured Data', {
            'fields': ('education', 'experience', 'skills', 'certifications', 'languages', 'projects'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('confidence_score', 'completion_percentage', 'parsed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'document')


class UserGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'priority', 'created_at')
    list_filter = ('goal', 'priority', 'created_at')
    search_fields = ('user__email',)
    ordering = ('user', 'priority')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(CareerProfile, CareerProfileAdmin)
admin.site.register(EducationProfile, EducationProfileAdmin)
admin.site.register(ExperienceProfile, ExperienceProfileAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(ParsedProfile, ParsedProfileAdmin)
admin.site.register(UserGoal, UserGoalAdmin)
