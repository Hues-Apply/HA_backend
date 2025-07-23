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
    degree_level = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
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
    
class ScholarshipProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    gpa = models.FloatField()
    location = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    degree_level = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    financial_need = models.FloatField()
    eligibility_tags = models.JSONField(default=list, blank=True)  

