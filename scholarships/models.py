from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Scholarship(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500)
    application_link = models.URLField(max_length=1000)
    source = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount_currency = models.CharField(max_length=3, default='USD', blank=True)
    deadline = models.DateField(null=True, blank=True)
    course = models.CharField(max_length=200)
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('4.00'))]
    )
    location = models.CharField(max_length=200)
    degree_level = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    scraped_at = models.DateTimeField()
    overview = models.TextField(blank=True, null=True)

    # Additional fields for better data management
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['deadline']),
            models.Index(fields=['amount']),
            models.Index(fields=['gpa']),
            models.Index(fields=['degree_level']),
            models.Index(fields=['location']),
        ]

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
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('4.00'))]
    )
    location = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    degree_level = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    financial_need = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    eligibility_tags = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Scholarship Profile"

