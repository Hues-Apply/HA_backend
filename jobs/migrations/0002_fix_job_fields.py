# Generated manually to fix job model field types and add proper structure

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        # Change field types from TextField to appropriate types
        migrations.AlterField(
            model_name='job',
            name='title',
            field=models.CharField(max_length=255, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='company',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),

        # Remove old salary field and add new salary fields
        migrations.RemoveField(
            model_name='job',
            name='salary',
        ),
        migrations.AddField(
            model_name='job',
            name='salary_min',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_max',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='salary_currency',
            field=models.CharField(blank=True, default='USD', max_length=3),
        ),

        migrations.AlterField(
            model_name='job',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='job',
            name='job_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('full-time', 'Full Time'),
                    ('part-time', 'Part Time'),
                    ('contract', 'Contract'),
                    ('internship', 'Internship'),
                    ('freelance', 'Freelance'),
                    ('temporary', 'Temporary'),
                ],
                max_length=20,
                null=True
            ),
        ),
        migrations.AlterField(
            model_name='job',
            name='experience_level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('entry', 'Entry Level'),
                    ('mid', 'Mid Level'),
                    ('senior', 'Senior Level'),
                    ('executive', 'Executive Level'),
                ],
                max_length=20,
                null=True
            ),
        ),

        # Add new fields for better data management
        migrations.AddField(
            model_name='job',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='requirements',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='benefits',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='application_url',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='is_remote',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='job',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='job',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='job',
            name='external_id',
            field=models.CharField(blank=True, max_length=255, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='job',
            name='source',
            field=models.CharField(
                choices=[
                    ('manual', 'Manual Entry'),
                    ('linkedin', 'LinkedIn'),
                    ('indeed', 'Indeed'),
                    ('glassdoor', 'Glassdoor'),
                    ('other', 'Other Source'),
                ],
                default='manual',
                max_length=50
            ),
        ),

        # Add indexes for better performance
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['title'], name='job_title_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['company'], name='job_company_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['location'], name='job_location_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['job_type'], name='job_type_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['experience_level'], name='job_experience_level_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['is_remote'], name='job_remote_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['is_active'], name='job_active_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['source'], name='job_source_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['posted_at'], name='job_posted_at_idx'),
        ),

        # Update UserJob model
        migrations.AddField(
            model_name='userjob',
            name='status',
            field=models.CharField(
                choices=[
                    ('applied', 'Applied'),
                    ('interviewing', 'Interviewing'),
                    ('offered', 'Offered'),
                    ('rejected', 'Rejected'),
                    ('withdrawn', 'Withdrawn'),
                ],
                default='applied',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='userjob',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),

        # Add indexes for UserJob
        migrations.AddIndex(
            model_name='userjob',
            index=models.Index(fields=['user', 'applied'], name='userjob_user_applied_idx'),
        ),
        migrations.AddIndex(
            model_name='userjob',
            index=models.Index(fields=['status'], name='userjob_status_idx'),
        ),
    ]
