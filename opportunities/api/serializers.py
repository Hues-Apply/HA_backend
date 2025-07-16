
from rest_framework import serializers
from opportunities.models import Category, Tag, Opportunity
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
from opportunities.models import OpportunityApplication

class SimpleJobSerializer(serializers.Serializer):
    company = serializers.CharField(required=True, allow_blank=False)
    title = serializers.CharField(required=True, allow_blank=False)
    location = serializers.CharField(required=True, allow_blank=False)
    link = serializers.CharField(required=True, allow_blank=False)
    # Optional fields
    type = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    details = serializers.JSONField(required=False, allow_null=True, default=None)
    jobID = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    company_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    # Add any other fields you expect from jobs_glassdoor.json as optional here

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class OpportunitySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    posted_by = serializers.StringRelatedField(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'type', 'organization', 'category', 'category_id',
            'location', 'is_remote', 'experience_level',
            'description', 'eligibility_criteria', 'skills_required',
            'tags', 'tag_ids', 'deadline', 'created_at',
            'is_verified', 'is_featured', 'application_url',
            'application_process', 'posted_by'
        ]
    def get_is_applied(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return OpportunityApplication.objects.filter(
                opportunity=obj,
                user=request.user
            ).exists()
        return False


class OpportunityRecommendationSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='opportunity.id')
    title = serializers.CharField(source='opportunity.title')
    type = serializers.CharField(source='opportunity.type')
    organization = serializers.CharField(source='opportunity.organization')
    category = serializers.SerializerMethodField()
    location = serializers.CharField(source='opportunity.location')
    is_remote = serializers.BooleanField(source='opportunity.is_remote')
    deadline = serializers.DateField(source='opportunity.deadline')
    experience_level = serializers.CharField(source='opportunity.experience_level')
    score = serializers.IntegerField()
    reasons = serializers.DictField()

    def get_category(self, obj):
        category = obj['opportunity'].category
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug
        }


class JobDataSerializer(serializers.Serializer):
    """Serializer for individual job data in bulk creation"""
    title = serializers.CharField(max_length=255)
    organization = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=255)
    description = serializers.CharField()
    type = serializers.CharField(max_length=50, default='job')
    category_name = serializers.CharField(max_length=100, required=False)
    deadline = serializers.DateField(required=False)
    salary_text = serializers.CharField(max_length=255, required=False, allow_blank=True)
    application_url = serializers.URLField(required=False, allow_blank=True)
    external_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    source = serializers.CharField(max_length=50, default='linkedin')
    experience_level = serializers.CharField(max_length=50, required=False, allow_blank=True)


class BulkJobCreateSerializer(serializers.Serializer):
    """Serializer for bulk job creation with validation and transformation"""
    jobs = JobDataSerializer(many=True)
    batch_id = serializers.CharField(max_length=100, required=False)
    auto_verify = serializers.BooleanField(default=False)
    skip_duplicates = serializers.BooleanField(default=True)

    def validate_jobs(self, value):
        """Validate that we have at least one job"""
        if not value:
            raise serializers.ValidationError("At least one job is required")
        if len(value) > 1000:
            raise serializers.ValidationError("Maximum 1000 jobs allowed per batch")
        return value

    def extract_skills_from_description(self, description):
        """Extract skills from job description using keyword matching"""
        # Common tech skills to look for
        skills_keywords = [
            'python', 'javascript', 'java', 'react', 'django', 'node.js', 'html', 'css',
            'sql', 'mongodb', 'postgresql', 'aws', 'docker', 'kubernetes', 'git',
            'machine learning', 'data science', 'ai', 'leadership', 'communication',
            'project management', 'agile', 'scrum', 'teamwork'
        ]

        found_skills = []
        description_lower = description.lower()

        for skill in skills_keywords:
            if skill in description_lower:
                found_skills.append(skill.title())

        return list(set(found_skills))  # Remove duplicates

    def parse_salary(self, salary_text):
        """Parse salary text and extract min, max, currency, and period"""
        if not salary_text:
            return None, None, None, None

        # Simple regex patterns for salary parsing
        import re

        # Look for currency symbols and amounts
        currency_patterns = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '₦': 'NGN'
        }

        currency = None
        for symbol, curr in currency_patterns.items():
            if symbol in salary_text:
                currency = curr
                break

        if not currency:
            currency = 'USD'  # Default

        # Extract numbers (simple approach)
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        amounts = [int(num) for num in numbers if num.isdigit()]

        if len(amounts) >= 2:
            salary_min = min(amounts)
            salary_max = max(amounts)
        elif len(amounts) == 1:
            salary_min = amounts[0]
            salary_max = amounts[0]
        else:
            salary_min = None
            salary_max = None

        # Determine period
        period = 'year'  # Default
        if any(word in salary_text.lower() for word in ['hour', 'hourly']):
            period = 'hour'
        elif any(word in salary_text.lower() for word in ['month', 'monthly']):
            period = 'month'

        return salary_min, salary_max, currency, period

    def detect_remote_work(self, location, description):
        """Detect if this is a remote work opportunity"""
        remote_keywords = ['remote', 'work from home', 'distributed', 'anywhere']

        location_lower = location.lower()
        description_lower = description.lower()

        return any(keyword in location_lower or keyword in description_lower
                  for keyword in remote_keywords)

    def get_or_create_category(self, category_name):
        """Get or create category by name"""
        try:
            return Category.objects.get(name__iexact=category_name)
        except Category.DoesNotExist:
            slug = slugify(category_name)
            return Category.objects.create(name=category_name, slug=slug)

    def get_or_create_tags(self, skills):
        """Get or create tags for skills"""
        tags = []
        for skill in skills:
            slug = slugify(skill)
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': skill}
            )
            tags.append(tag)
        return tags

    def check_duplicate(self, title, organization, external_id=None):
        """Check if opportunity already exists"""
        queryset = Opportunity.objects.filter(
            title__iexact=title,
            organization__iexact=organization
        )

        if external_id:
            queryset = queryset.filter(external_id=external_id)

        return queryset.exists()

    def transform_job_data(self, job_data, batch_id=None, user=None):
        """Transform individual job data into Opportunity model format"""
        # Extract and parse data
        skills = self.extract_skills_from_description(job_data['description'])
        salary_min, salary_max, currency, period = self.parse_salary(
            job_data.get('salary_text', '')
        )
        is_remote = self.detect_remote_work(
            job_data['location'],
            job_data['description']
        )

        # Get or create category
        category = self.get_or_create_category(
            job_data.get('category_name', 'Technology')
        )

        # Set deadline (default to 30 days from now if not provided)
        deadline = job_data.get('deadline')
        if not deadline:
            deadline = timezone.now().date() + timedelta(days=30)

        # Prepare the opportunity data
        opportunity_data = {
            'title': job_data['title'],
            'type': job_data.get('type', 'job'),
            'organization': job_data['organization'],
            'category': category,
            'location': job_data['location'],
            'is_remote': is_remote,
            'description': job_data['description'],
            'skills_required': skills,
            'deadline': deadline,
            'application_url': job_data.get('application_url', ''),
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': currency,
            'salary_period': period,
            'external_id': job_data.get('external_id', ''),
            'source': job_data.get('source', 'linkedin'),
            'import_batch_id': batch_id,
            'posted_by': user if user and user.is_authenticated else None,
            'is_verified': False,  # Will be set based on auto_verify flag
            'experience_level': job_data.get('experience_level', ''),
        }

        return opportunity_data, skills

    def create(self, validated_data):
        """Create opportunities in bulk with transaction safety"""
        from django.db import transaction

        jobs_data = validated_data['jobs']
        batch_id = validated_data.get('batch_id', f"batch_{timezone.now().strftime('%Y%m%d_%H%M%S')}")
        auto_verify = validated_data.get('auto_verify', False)
        skip_duplicates = validated_data.get('skip_duplicates', True)
        user = self.context.get('user')

        created_opportunities = []
        skipped_count = 0
        errors = []

        with transaction.atomic():
            for i, job_data in enumerate(jobs_data):
                try:
                    # Check for duplicates
                    if skip_duplicates and self.check_duplicate(
                        job_data['title'],
                        job_data['organization'],
                        job_data.get('external_id')
                    ):
                        skipped_count += 1
                        continue

                    # Transform job data
                    opportunity_data, skills = self.transform_job_data(
                        job_data, batch_id, user
                    )

                    # Set verification status
                    opportunity_data['is_verified'] = auto_verify

                    # Create opportunity
                    opportunity = Opportunity.objects.create(**opportunity_data)

                    # Add tags (skills)
                    if skills:
                        tags = self.get_or_create_tags(skills)
                        opportunity.tags.set(tags)

                    created_opportunities.append(opportunity)

                except Exception as e:
                    errors.append({
                        'index': i,
                        'title': job_data.get('title', 'Unknown'),
                        'error': str(e)
                    })

        return {
            'created_count': len(created_opportunities),
            'skipped_count': skipped_count,
            'error_count': len(errors),
            'errors': errors,
            'batch_id': batch_id,
            'opportunities': created_opportunities
        }


class JobScrapingRequestSerializer(serializers.Serializer):
    """
    Serializer for JobSpy scraping requests.
    Validates parameters for job scraping from various platforms.
    """

    VALID_SITES = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google', 'bayt', 'naukri']
    JOB_TYPE_CHOICES = ['fulltime', 'parttime', 'internship', 'contract']

    site_names = serializers.ListField(
        child=serializers.ChoiceField(choices=VALID_SITES),
        default=['indeed', 'linkedin', 'glassdoor'],
        help_text="List of job sites to scrape from"
    )

    location = serializers.CharField(
        max_length=255,
        default='United States',
        help_text="Location to search for jobs"
    )

    search_term = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional search term to filter jobs (leave empty to get all job types)"
    )

    job_type = serializers.ChoiceField(
        choices=JOB_TYPE_CHOICES,
        required=False,
        help_text="Type of employment to filter by"
    )

    results_wanted = serializers.IntegerField(
        default=50,
        min_value=1,
        max_value=1000,
        help_text="Number of job results to retrieve per site (1-1000)"
    )

    hours_old = serializers.IntegerField(
        default=168,  # 1 week
        min_value=1,
        max_value=8760,  # 1 year
        help_text="Filter jobs posted within this many hours (1-8760)"
    )

    is_remote = serializers.BooleanField(
        default=False,
        help_text="Filter for remote jobs only"
    )

    country_indeed = serializers.CharField(
        max_length=50,
        default='USA',
        help_text="Country code for Indeed/Glassdoor searches"
    )

    linkedin_fetch_description = serializers.BooleanField(
        default=False,
        help_text="Fetch full descriptions for LinkedIn jobs (slower but more detailed)"
    )

    proxies = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True,
        help_text="List of proxy URLs in format 'user:pass@host:port'"
    )

    dry_run = serializers.BooleanField(
        default=False,
        help_text="Return scraped data without saving to database"
    )

    def validate_site_names(self, value):
        """Ensure at least one valid site is provided"""
        if not value:
            raise serializers.ValidationError("At least one site must be specified")
        return value

    def validate_proxies(self, value):
        """Validate proxy format"""
        if not value:
            return value

        for proxy in value:
            # Basic validation for proxy format
            if not re.match(r'^(?:[\w\-\.]+:[\w\-\.]+@)?[\w\-\.]+:\d+$', proxy):
                raise serializers.ValidationError(
                    f"Invalid proxy format: {proxy}. Expected format: 'user:pass@host:port' or 'host:port'"
                )
        return value


class JobScrapingResponseSerializer(serializers.Serializer):
    """
    Serializer for JobSpy scraping response data.
    """
    success = serializers.BooleanField()
    message = serializers.CharField()
    stats = serializers.DictField()
    sample_data = serializers.ListField(required=False)
    errors = serializers.ListField(required=False)
    created_opportunity_ids = serializers.ListField(required=False)


class OpportunityApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityApplication
        fields = ['id', 'user', 'opportunity', 'applied_at']

