from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Job, UserJob

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'salary', 'location', 'job_type', 'experience_level', 'posted_at')
    search_fields = ('title', 'company', 'skills', 'location', 'job_type')
    list_filter = ('location', 'job_type', 'experience_level')
    ordering = ('-posted_at',)


@admin.register(UserJob)
class UserJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'job', 'applied', 'applied_date', 'updated_at')
    list_filter = ('applied', 'applied_date')
    search_fields = ('user__email', 'job__title')
