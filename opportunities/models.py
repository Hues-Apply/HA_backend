from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models import JSONField
from django.utils.text import slugify
from django.core.cache import cache
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.cache import cache
from opportunities.models import Category, Tag

class Opportunity(models.Model):
    OPPORTUNITY_TYPES = (
        ('job', 'Job'),
        ('scholarship', 'Scholarship'),
        ('grant', 'Grant'),
        ('internship', 'Internship'),
        ('fellowship', 'Fellowship'),
    )

    EXPERIENCE_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
    ]

    title = models.CharField(max_length=255, db_index=True)
    type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPES, db_index=True)
    organization = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='opportunities')
    location = models.CharField(max_length=100, db_index=True)
    is_remote = models.BooleanField(default=False)
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='entry',
        db_index=True
    )
    description = models.TextField()
    eligibility_criteria = models.JSONField(default=dict)
    skills_required = ArrayField(models.CharField(max_length=50), blank=True, default=list)
    tags = models.ManyToManyField(Tag, related_name='opportunities', blank=True)
    deadline = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    search_vector = SearchVectorField(null=True)
    view_count = models.PositiveIntegerField(default=0)
    application_count = models.PositiveIntegerField(default=0)
    application_url = models.URLField(blank=True)
    application_process = models.TextField(blank=True)

    # Salary fields
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='USD', blank=True)
    salary_period = models.CharField(max_length=20, choices=[
        ('hourly', 'Per Hour'),
        ('daily', 'Per Day'),
        ('weekly', 'Per Week'),
        ('monthly', 'Per Month'),
        ('yearly', 'Per Year'),
    ], default='yearly', blank=True)

    # Additional fields for bulk import
    external_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    source = models.CharField(max_length=50, default='manual', choices=[
        ('manual', 'Manual Entry'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('glassdoor', 'Glassdoor'),
        ('other', 'Other Source'),
    ])
    import_batch_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.organization}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Opportunity.objects.filter(pk=self.pk).update(
            search_vector=SearchVector('title', 'description', 'organization')
        )
        cache.delete_pattern('recommendations_*')

    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deadline']),
            models.Index(fields=['type', 'deadline']),
            models.Index(fields=['location']),
        ]

class OpportunityApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'opportunity')
        verbose_name = "Applied Opportunity"
        verbose_name_plural = "Applied Opportunities"

    def __str__(self):
        return f"{self.user.email} applied for {self.opportunity.title}"
