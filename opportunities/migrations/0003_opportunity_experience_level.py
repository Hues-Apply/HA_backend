# Generated by Django 5.2.1 on 2025-07-08 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opportunities', '0002_opportunity_posted_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='opportunity',
            name='experience_level',
            field=models.CharField(choices=[('entry', 'Entry Level'), ('mid', 'Mid Level'), ('senior', 'Senior Level')], db_index=True, default='entry', max_length=20),
        ),
    ]
