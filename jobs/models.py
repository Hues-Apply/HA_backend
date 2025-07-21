from django.db import models
from django.conf import settings

class Job(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField()
    company = models.TextField(blank=True, null=True)
    salary = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    job_type = models.TextField(blank=True, null=True)  # Full-time, Part-time, etc.
    skills = models.TextField(blank=True, null=True)  # Required skills (comma-separated or plain text)
    experience_level = models.TextField(blank=True, null=True)  # Fresher, Mid, Senior, etc.
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class UserJob(models.Model):
    """Model to track user job applications"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applied = models.BooleanField(default=False)
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'job']
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.user.email} - {self.job.title}"
