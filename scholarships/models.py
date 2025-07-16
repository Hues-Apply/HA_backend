from django.db import models
from django.conf import settings

class Scholarship(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField()
    application_link = models.TextField()
    source = models.TextField()
    amount = models.TextField()
    deadline = models.TextField()
    course = models.TextField()
    gpa = models.TextField()
    location = models.TextField()
    scraped_at = models.DateTimeField()
    overview = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

class UserScholarship(models.Model):
    """Model to track user scholarship applications"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scholarship_applications')
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, related_name='applications')
    applied = models.BooleanField(default=False)
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'scholarship']
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.user.email} - {self.scholarship.title}"
