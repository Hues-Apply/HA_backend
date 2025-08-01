# Generated manually to fix scholarship model field types and add constraints

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('scholarships', '0004_scholarship_degree_level_scholarship_nationality_and_more'),
    ]

    operations = [
        # Add new fields for better data management (these are safe to add)
        migrations.AddField(
            model_name='scholarship',
            name='amount_currency',
            field=models.CharField(max_length=3, default='USD'),
        ),
        migrations.AddField(
            model_name='scholarship',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='scholarship',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='scholarship',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),

        # Add indexes for better performance (these are safe to add)
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['deadline'], name='scholarship_deadline_idx'),
        ),
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['amount'], name='scholarship_amount_idx'),
        ),
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['gpa'], name='scholarship_gpa_idx'),
        ),
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['degree_level'], name='scholarship_degree_level_idx'),
        ),
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['location'], name='scholarship_location_idx'),
        ),
        migrations.AddIndex(
            model_name='scholarship',
            index=models.Index(fields=['is_active', 'deadline'], name='scholarship_active_deadline_idx'),
        ),

        # Update ScholarshipProfile model (safe changes)
        migrations.AddField(
            model_name='scholarshipprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='scholarshipprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
