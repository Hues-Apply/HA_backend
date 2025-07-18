# Generated by Django 5.2.1 on 2025-05-18 10:14

import django.contrib.postgres.fields
import django.contrib.postgres.search
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Opportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=255)),
                ('type', models.CharField(choices=[('job', 'Job'), ('scholarship', 'Scholarship'), ('grant', 'Grant'), ('internship', 'Internship'), ('fellowship', 'Fellowship')], db_index=True, max_length=20)),
                ('organization', models.CharField(max_length=255)),
                ('location', models.CharField(db_index=True, max_length=100)),
                ('is_remote', models.BooleanField(default=False)),
                ('description', models.TextField()),
                ('eligibility_criteria', models.JSONField(default=dict)),
                ('skills_required', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), blank=True, default=list, size=None)),
                ('deadline', models.DateField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_verified', models.BooleanField(default=False)),
                ('is_featured', models.BooleanField(default=False)),
                ('search_vector', django.contrib.postgres.search.SearchVectorField(null=True)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('application_count', models.PositiveIntegerField(default=0)),
                ('application_url', models.URLField(blank=True)),
                ('application_process', models.TextField(blank=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunities', to='opportunities.category')),
                ('tags', models.ManyToManyField(blank=True, related_name='opportunities', to='opportunities.tag')),
            ],
            options={
                'verbose_name_plural': 'Opportunities',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['deadline'], name='opportuniti_deadlin_294f61_idx'), models.Index(fields=['type', 'deadline'], name='opportuniti_type_b12eb2_idx'), models.Index(fields=['location'], name='opportuniti_locatio_df5b7c_idx')],
            },
        ),
    ]
