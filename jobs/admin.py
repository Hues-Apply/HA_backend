from django.contrib import admin
from .models import Job, UserJob

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'salary_min', 'salary_max', 'location', 'job_type', 'experience_level', 'is_active', 'posted_at')
    search_fields = ('title', 'company', 'skills', 'location', 'job_type', 'description')
    list_filter = ('location', 'job_type', 'experience_level', 'is_remote', 'is_active', 'source')
    ordering = ('-posted_at',)
    readonly_fields = ('posted_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'description', 'requirements', 'benefits')
        }),
        ('Location & Type', {
            'fields': ('location', 'is_remote', 'job_type', 'experience_level')
        }),
        ('Salary Information', {
            'fields': ('salary_min', 'salary_max', 'salary_currency'),
            'classes': ('collapse',)
        }),
        ('Skills & Requirements', {
            'fields': ('skills',),
            'classes': ('collapse',)
        }),
        ('Application', {
            'fields': ('application_url',)
        }),
        ('Metadata', {
            'fields': ('external_id', 'source', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('posted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserJob)
class UserJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'status', 'applied', 'applied_date', 'updated_at')
    list_filter = ('status', 'applied', 'applied_date', 'updated_at')
    search_fields = ('user__email', 'job__title', 'notes')
    readonly_fields = ('applied_date', 'updated_at')

    fieldsets = (
        ('Application Details', {
            'fields': ('user', 'job', 'status', 'applied')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('applied_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
