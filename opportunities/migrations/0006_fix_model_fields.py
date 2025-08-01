# Generated manually to fix model field types and add constraints

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0005_remove_opportunity_posted_by_opportunityapplication'),
    ]

    operations = [
        # Add only the missing is_active field
        migrations.AddField(
            model_name='opportunity',
            name='is_active',
            field=models.BooleanField(default=True),
        ),

        # Add indexes for better performance (these should be safe to add)
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['type', 'deadline'], name='opportunity_type_deadline_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['location', 'is_remote'], name='opportunity_location_remote_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['experience_level', 'type'], name='opportunity_exp_type_idx'),
        ),
        migrations.AddIndex(
            model_name='opportunity',
            index=models.Index(fields=['is_active', 'deadline'], name='opportunity_active_deadline_idx'),
        ),
    ]
