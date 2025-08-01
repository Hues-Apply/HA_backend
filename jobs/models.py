from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Job(models.Model):
    JOB_TYPES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
        ('temporary', 'Temporary'),
    ]

    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive Level'),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, db_index=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD', blank=True)
    location = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)  # Required skills (comma-separated or plain text)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    application_url = models.URLField(max_length=1000, blank=True, null=True)
    is_remote = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional fields for better data management
    external_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    source = models.CharField(max_length=50, default='manual', choices=[
        ('manual', 'Manual Entry'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('other', 'Other Source'),
    ])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company']),
            models.Index(fields=['location']),
            models.Index(fields=['job_type']),
            models.Index(fields=['experience_level']),
            models.Index(fields=['is_remote']),
            models.Index(fields=['is_active']),
            models.Index(fields=['source']),
        ]

class UserJob(models.Model):
    """Model to track user job applications"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applied = models.BooleanField(default=False)
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Additional tracking fields
    status = models.CharField(max_length=20, default='applied', choices=[
        ('applied', 'Applied'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ])
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-applied_date']
        indexes = [
            models.Index(fields=['user', 'applied']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.job.title}"
