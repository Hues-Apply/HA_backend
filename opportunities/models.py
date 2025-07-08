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
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="opportunities_posted",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.get_type_display()}) - {self.organization}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Opportunity.objects.filter(pk=self.pk).update(
            search_vector=SearchVector('title', 'description', 'organization')
        )
        cache_keys = [f'user_recommendations_{user_id}' for user_id in range(1, 1000)]
        cache.delete_many(cache_keys)

    class Meta:
        verbose_name_plural = "Opportunities"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deadline']),
            models.Index(fields=['type', 'deadline']),
            models.Index(fields=['location']),
        ]

