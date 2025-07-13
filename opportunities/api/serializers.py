from rest_framework import serializers
from opportunities.models import Category, Tag, Opportunity
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class OpportunitySerializer(serializers.ModelSerializer):
    # For readable output
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    posted_by = serializers.StringRelatedField(read_only=True)

    # For input (write)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'type', 'organization', 'category', 'category_id', 'location', 'is_remote', 'description', 'eligibility_criteria', 'skills_required', 'tags', 'tag_ids', 'deadline', 'created_at', 'is_verified', 'is_featured', 'application_url', 'application_process', 'posted_by'
        ]

class OpportunityRecommendationSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='opportunity.id')
    title = serializers.CharField(source='opportunity.title')
    type = serializers.CharField(source='opportunity.type')
    organization = serializers.CharField(source='opportunity.organization')
    category = serializers.SerializerMethodField()
    location = serializers.CharField(source='opportunity.location')
    is_remote = serializers.BooleanField(source='opportunity.is_remote')
    deadline = serializers.DateField(source='opportunity.deadline')
    score = serializers.IntegerField()
    reasons = serializers.DictField()
    
    def get_category(self, obj):
        return {
            'id': obj['opportunity'].category.id,
            'name': obj['opportunity'].category.name,
            'slug': obj['opportunity'].category.slug
        }

class BulkJobItemSerializer(serializers.Serializer):
    """Serializer for individual job items in bulk creation"""
    title = serializers.CharField(max_length=255)
    organization = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=100)
    description = serializers.CharField()
    application_url = serializers.URLField(required=False, allow_blank=True)
    external_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    deadline = serializers.DateField(required=False, allow_null=True)
    salary_text = serializers.CharField(required=False, allow_blank=True)
    
    # Optional fields
    type = serializers.ChoiceField(choices=Opportunity.OPPORTUNITY_TYPES, default='job')
    category_name = serializers.CharField(max_length=100, required=False, default='Technology')
    source = serializers.CharField(max_length=50, default='linkedin')


class BulkJobCreateSerializer(serializers.Serializer):
    """Serializer for bulk job creation with data validation and transformation"""
    jobs = BulkJobItemSerializer(many=True)
    batch_id = serializers.CharField(max_length=100, required=False)
    auto_verify = serializers.BooleanField(default=False)
    skip_duplicates = serializers.BooleanField(default=True)
    
    def validate_jobs(self, value):
        """Validate job data and check for duplicates within the batch"""
        if not value:
            raise serializers.ValidationError("At least one job must be provided")
        
        if len(value) > 1000:
            raise serializers.ValidationError("Maximum 1000 jobs allowed per batch")
        
        # Check for duplicates within the batch
        seen_combinations = set()
        for job in value:
            key = (job.get('title', '').lower(), job.get('organization', '').lower())
            if key in seen_combinations:
                raise serializers.ValidationError(
                    f"Duplicate job found: {job.get('title')} at {job.get('organization')}"
                )
            seen_combinations.add(key)
        
        return value

    def extract_skills_from_description(self, description):
        """Extract skills from job description using keyword matching"""
        # Common tech skills to look for
        skill_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Angular', 'Vue',
            'Node.js', 'Django', 'Flask', 'Spring', 'Laravel', 'PHP', 'Ruby',
            'C++', 'C#', '.NET', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala',
            'HTML', 'CSS', 'Bootstrap', 'Tailwind', 'SASS', 'LESS',
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'ElasticSearch',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins',
            'Git', 'GitHub', 'GitLab', 'Jira', 'Confluence',
            'Machine Learning', 'AI', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'Data Science', 'Analytics', 'Tableau', 'Power BI',
            'Agile', 'Scrum', 'DevOps', 'CI/CD', 'Testing', 'QA',
            'Project Management', 'Leadership', 'Communication', 'Teamwork'
        ]
        
        found_skills = []
        description_lower = description.lower()
        
        for skill in skill_keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, description_lower):
                found_skills.append(skill)
        
        return found_skills[:10]  # Limit to 10 skills to avoid overcrowding

    def parse_salary(self, salary_text):
        """Parse salary text and extract min, max, currency, and period"""
        if not salary_text:
            return None, None, 'USD', 'yearly'
        
        # Remove common prefixes/suffixes
        text = salary_text.lower().strip()
        text = re.sub(r'(salary|compensation|pay|wage):\s*', '', text)
        
        # Extract currency
        currency = 'USD'
        if '€' in text or 'eur' in text:
            currency = 'EUR'
        elif '£' in text or 'gbp' in text:
            currency = 'GBP'
        elif '₦' in text or 'ngn' in text or 'naira' in text:
            currency = 'NGN'
        
        # Extract period
        period = 'yearly'
        if any(word in text for word in ['hour', 'hr', 'hourly']):
            period = 'hourly'
        elif any(word in text for word in ['month', 'monthly']):
            period = 'monthly'
        elif any(word in text for word in ['week', 'weekly']):
            period = 'weekly'
        elif any(word in text for word in ['day', 'daily']):
            period = 'daily'
        
        # Extract numbers using regex
        numbers = re.findall(r'[\d,]+(?:\.\d{2})?', text.replace(',', ''))
        numbers = [float(n) for n in numbers if n]
        
        if not numbers:
            return None, None, currency, period
        
        # If only one number, use it as both min and max
        if len(numbers) == 1:
            return numbers[0], numbers[0], currency, period
        
        # If multiple numbers, use min and max
        return min(numbers), max(numbers), currency, period

    def detect_remote_work(self, location, description):
        """Detect if job is remote based on location and description"""
        location_lower = location.lower()
        description_lower = description.lower()
        
        remote_indicators = [
            'remote', 'work from home', 'wfh', 'telecommute', 'distributed',
            'virtual', 'anywhere', 'global', 'home-based'
        ]
        
        # Check location
        for indicator in remote_indicators:
            if indicator in location_lower:
                return True
        
        # Check description
        for indicator in remote_indicators:
            if indicator in description_lower:
                return True
        
        return False

    def get_or_create_category(self, category_name):
        """Get or create category for the job"""
        try:
            return Category.objects.get(name__iexact=category_name)
        except Category.DoesNotExist:
            return Category.objects.create(
                name=category_name,
                slug=slugify(category_name)
            )

    def get_or_create_tags(self, skills):
        """Get or create tags for the skills"""
        tags = []
        for skill in skills:
            tag, created = Tag.objects.get_or_create(
                name=skill,
                defaults={'slug': slugify(skill)}
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
                        'job_index': i,
                        'title': job_data.get('title', 'Unknown'),
                        'error': str(e)
                    })
        
        return {
            'created_count': len(created_opportunities),
            'skipped_count': skipped_count,
            'error_count': len(errors),
            'batch_id': batch_id,
            'opportunities': created_opportunities,
            'errors': errors
        }

