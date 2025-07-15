from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Count, Q, Avg, Sum
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
import hashlib
import json
import uuid
import re
from datetime import timedelta, datetime
from django.db import transaction
from .serializers import (
    OpportunitySerializer, 
    OpportunityRecommendationSerializer, 
    BulkJobCreateSerializer,
    JobScrapingRequestSerializer
)
from opportunities.matching import OpportunityMatcher
from opportunities.models import Opportunity


class OpportunityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OpportunityViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def from_jobs_json(self, request):
        """
        Loads and merges opportunities from jobs.json and jobs_glassdoor.json, returns as a list.
        This is for development/testing/demo purposes only.
        """
        import os
        import json
        from django.conf import settings
        from .serializers import SimpleJobSerializer

        base_dir = os.path.dirname(__file__)
        jobs_json_path = os.path.join(base_dir, 'jobs.json')
        glassdoor_json_path = os.path.join(base_dir, 'jobs_glassdoor.json')

        jobs = []

        # Load jobs.json
        if os.path.exists(jobs_json_path):
            with open(jobs_json_path, 'r', encoding='utf-8') as f:
                try:
                    jobs_data = json.load(f)
                    # jobs.json: if dict with 'data' key, use that
                    if isinstance(jobs_data, dict) and 'data' in jobs_data:
                        jobs += jobs_data['data']
                    else:
                        jobs += jobs_data
                except Exception as e:
                    return Response({"error": f"Failed to parse jobs.json: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        # If not found, skip

        # Load jobs_glassdoor.json
        if os.path.exists(glassdoor_json_path):
            with open(glassdoor_json_path, 'r', encoding='utf-8') as f:
                try:
                    glassdoor_data = json.load(f)
                    # jobs_glassdoor.json is a list
                    if isinstance(glassdoor_data, list):
                        jobs += glassdoor_data
                except Exception as e:
                    return Response({"error": f"Failed to parse jobs_glassdoor.json: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not jobs:
            return Response({"error": "No jobs found in either file."}, status=status.HTTP_404_NOT_FOUND)

        # Use SimpleJobSerializer(many=True) for consistent API format
        serializer = SimpleJobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    serializer_class = OpportunitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OpportunityPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'type', 'location', 'is_remote', 'category__slug', 'tags__slug',
        'deadline', 'experience_level'  
    ]
    search_fields = ['title', 'description', 'organization']
    ordering_fields = ['deadline', 'created_at', 'title', 'view_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Opportunity.objects.all()

        search_query = self.request.query_params.get('search')
        if search_query:
            query = SearchQuery(search_query)
            queryset = queryset.annotate(rank=SearchRank(F('search_vector'), query)) \
                            .filter(search_vector=query) \
                            .order_by('-rank')

        skills = self.request.query_params.getlist('skills')
        if skills:
            for skill in skills:
                queryset = queryset.filter(skills_required__contains=[skill])

        education_level = self.request.query_params.get('education_level')
        if education_level:
            queryset = queryset.filter(eligibility_criteria__education_level=education_level)

        show_expired = self.request.query_params.get('show_expired', 'false').lower()
        if show_expired != 'true':
            queryset = queryset.filter(deadline__gte=timezone.now().date())

        posted_within = self.request.query_params.get('posted_within')
        if posted_within:
            try:
                hours = int(posted_within.replace('h', ''))
                since = timezone.now() - timezone.timedelta(hours=hours)
                queryset = queryset.filter(created_at__gte=since)
            except ValueError:
                pass

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def recommended(self, request):
        """
        Returns personalized recommendations based on user profile and preferences,
        supports caching, ordering, and pagination.
        Note: Currently public for development, will require authentication later.
        """
        # TODO: Implement proper authentication check
        if not hasattr(request.user, 'profile') or not request.user.is_authenticated:
            return Response(
                {"error": "User profile required for recommendations"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        user_profile = request.user.profile
        filters_dict = {}
        for param in ['type', 'location', 'category', 'experience_level']:
            val = request.query_params.get(param)
            if val:
                filters_dict[param] = val

        tags = request.query_params.getlist('tags')
        if tags:
            filters_dict['tags'] = tags

        skills = request.query_params.getlist('skills')
        if skills:
            filters_dict['skills'] = skills

        deadline_after = request.query_params.get('deadline_after')
        if deadline_after:
            filters_dict['deadline_after'] = deadline_after

        deadline_before = request.query_params.get('deadline_before')
        if deadline_before:
            filters_dict['deadline_before'] = deadline_before

        posted_within = request.query_params.get('posted_within')  
        if posted_within:
            filters_dict['posted_within'] = posted_within

        ordering = request.query_params.get('ordering', '-score')

        # Build cache key
        cache_key_raw = {
            'user_id': request.user.id,
            'filters': filters_dict,
            'ordering': ordering
        }
        cache_key = 'recommendations_' + hashlib.md5(json.dumps(cache_key_raw, sort_keys=True).encode()).hexdigest()
        cached_data = cache.get(cache_key)
        if cached_data:
            return self.get_paginated_response(cached_data)

        matcher = OpportunityMatcher(user_profile)
        recommendations = matcher.get_recommended_opportunities(filters=filters_dict)

        allowed_order_fields = {'score', 'deadline', 'title'}
        reverse = ordering.startswith('-')
        order_field = ordering.lstrip('-')

        if order_field not in allowed_order_fields:
            order_field = 'score'

        recommendations = sorted(
            recommendations,
            key=lambda rec: rec.get(order_field) if isinstance(rec, dict) else getattr(rec, order_field, None),
            reverse=reverse
        )

        page = self.paginate_queryset(recommendations)
        if page is not None:
            serializer = OpportunityRecommendationSerializer(page, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=300)
            return self.get_paginated_response(data)

        serializer = OpportunityRecommendationSerializer(recommendations, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=300)
        return Response(data)

    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.view_count = F('view_count') + 1
        opportunity.save(update_fields=['view_count'])
        opportunity.refresh_from_db(fields=['view_count'])
        return Response({'status': 'view tracked', 'view_count': opportunity.view_count})

    @action(detail=True, methods=['post'])
    def track_application(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.application_count = F('application_count') + 1
        opportunity.save(update_fields=['application_count'])
        opportunity.refresh_from_db(fields=['application_count'])
        return Response({'status': 'application tracked', 'application_count': opportunity.application_count})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def bulk_create(self, request):
        """
        Bulk create opportunities with data validation and transformation.
        Supports automatic skill extraction, salary parsing, and duplicate prevention.
        Note: Currently public for development, will require proper authentication later.
        """
        # TODO: Implement proper permission checks
        # if not request.user.is_staff and not request.user.groups.filter(name='Employers').exists():
        #     return Response(
        #         {"error": "Permission denied. Only employers and staff can bulk create opportunities."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        serializer = BulkJobCreateSerializer(
            data=request.data,
            context={'user': getattr(request, 'user', None)}
        )
        
        if serializer.is_valid():
            try:
                result = serializer.save()
                
                # Clear recommendation cache for all users
                cache_pattern = 'user_recommendations_*'
                cache.delete_pattern(cache_pattern)
                
                response_data = {
                    'success': True,
                    'message': f"Bulk creation completed successfully",
                    'stats': {
                        'created_count': result['created_count'],
                        'skipped_count': result['skipped_count'],
                        'error_count': result['error_count'],
                        'batch_id': result['batch_id']
                    }
                }
                
                # Include errors if any
                if result['errors']:
                    response_data['errors'] = result['errors']
                
                # Include created opportunity IDs for tracking
                response_data['created_opportunity_ids'] = [
                    opp.id for opp in result['opportunities']
                ]
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response(
                    {"error": f"Bulk creation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def crawl_stats(self, request):
        """
        Get dashboard statistics for opportunity crawling and creation.
        Provides insights into data sources, verification status, and recent activity.
        Note: Currently public for development, will require staff authentication later.
        """
        # TODO: Implement proper staff permission check
        # if not request.user.is_staff:
        #     return Response(
        #         {"error": "Permission denied. Only staff can view crawl statistics."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        try:
            # Get date ranges for statistics
            now = timezone.now()
            today = now.date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Basic counts
            total_opportunities = Opportunity.objects.count()
            verified_count = Opportunity.objects.filter(is_verified=True).count()
            unverified_count = total_opportunities - verified_count
            
            # Source breakdown
            source_stats = Opportunity.objects.values('source').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Recent activity (last 30 days)
            recent_opportunities = Opportunity.objects.filter(
                created_at__date__gte=month_ago
            )
            
            recent_by_day = recent_opportunities.extra(
                select={'day': 'date(created_at)'
            }).values('day').annotate(
                count=Count('id')
            ).order_by('day')
            
            # Batch statistics
            batch_stats = Opportunity.objects.filter(
                import_batch_id__isnull=False,
                created_at__date__gte=month_ago
            ).values('import_batch_id', 'source').annotate(
                count=Count('id'),
                verified_count=Count('id', filter=Q(is_verified=True))
            ).order_by('-count')[:10]
            
            # Type distribution
            type_stats = Opportunity.objects.values('type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Location insights (top 10)
            location_stats = Opportunity.objects.exclude(
                location__iexact='remote'
            ).values('location').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Remote vs on-site breakdown
            remote_count = Opportunity.objects.filter(is_remote=True).count()
            onsite_count = total_opportunities - remote_count
            
            # Category breakdown
            category_stats = Opportunity.objects.values(
                'category__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Salary insights
            opportunities_with_salary = Opportunity.objects.filter(
                salary_min__isnull=False
            ).count()
            
            salary_by_currency = Opportunity.objects.filter(
                salary_min__isnull=False
            ).values('salary_currency').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Performance metrics
            avg_view_count = Opportunity.objects.aggregate(
                avg_views=Avg('view_count')
            )['avg_views'] or 0
            
            avg_application_count = Opportunity.objects.aggregate(
                avg_applications=Avg('application_count')
            )['avg_applications'] or 0
            
            stats = {
                'overview': {
                    'total_opportunities': total_opportunities,
                    'verified_count': verified_count,
                    'unverified_count': unverified_count,
                    'verification_rate': round(verified_count / total_opportunities * 100, 2) if total_opportunities > 0 else 0,
                    'opportunities_with_salary': opportunities_with_salary,
                    'salary_coverage': round(opportunities_with_salary / total_opportunities * 100, 2) if total_opportunities > 0 else 0
                },
                'sources': {
                    'breakdown': list(source_stats),
                    'total_sources': len(source_stats)
                },
                'recent_activity': {
                    'last_30_days': recent_opportunities.count(),
                    'last_7_days': Opportunity.objects.filter(created_at__date__gte=week_ago).count(),
                    'today': Opportunity.objects.filter(created_at__date=today).count(),
                    'daily_breakdown': list(recent_by_day)
                },
                'batch_imports': {
                    'recent_batches': list(batch_stats),
                    'total_batches': Opportunity.objects.filter(
                        import_batch_id__isnull=False
                    ).values('import_batch_id').distinct().count()
                },
                'content_distribution': {
                    'by_type': list(type_stats),
                    'by_category': list(category_stats),
                    'by_location': list(location_stats),
                    'remote_vs_onsite': {
                        'remote': remote_count,
                        'onsite': onsite_count,
                        'remote_percentage': round(remote_count / total_opportunities * 100, 2) if total_opportunities > 0 else 0
                    }
                },
                'salary_insights': {
                    'by_currency': list(salary_by_currency),
                    'coverage_percentage': round(opportunities_with_salary / total_opportunities * 100, 2) if total_opportunities > 0 else 0
                },
                'performance': {
                    'avg_view_count': round(avg_view_count, 2),
                    'avg_application_count': round(avg_application_count, 2),
                    'total_views': Opportunity.objects.aggregate(
                        total=Sum('view_count')
                    )['total'] or 0,
                    'total_applications': Opportunity.objects.aggregate(
                        total=Sum('application_count')
                    )['total'] or 0
                },
                'data_quality': {
                    'opportunities_with_external_id': Opportunity.objects.filter(
                        external_id__isnull=False
                    ).exclude(external_id='').count(),
                    'opportunities_with_tags': Opportunity.objects.filter(
                        tags__isnull=False
                    ).distinct().count(),
                    'opportunities_with_skills': Opportunity.objects.exclude(
                        skills_required=[]
                    ).count()
                },
                'generated_at': now.isoformat()
            }
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to generate crawl statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def scrape_jobs(self, request):
        """
        Scrape jobs from various job boards using JobSpy library.
        Accepts parameters for customizing the scraping process.
        Note: Currently public for development, will require proper authentication later.
        """
        # TODO: Implement proper permission checks
        # if not request.user.is_staff and not request.user.groups.filter(name='Employers').exists():
        #     return Response(
        #         {"error": "Permission denied. Only employers and staff can scrape jobs."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        try:
            from jobspy import scrape_jobs
        except ImportError:
            return Response(
                {"error": "JobSpy library is not installed. Please install with: pip install python-jobspy"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate parameters
        site_names = request.data.get('site_names', ['indeed', 'linkedin', 'glassdoor'])
        location = request.data.get('location', 'United States')
        job_type = request.data.get('job_type')  # fulltime, parttime, internship, contract
        results_wanted = request.data.get('results_wanted', 50)
        hours_old = request.data.get('hours_old', 168)  # 1 week default
        is_remote = request.data.get('is_remote', False)
        country_indeed = request.data.get('country_indeed', 'USA')
        linkedin_fetch_description = request.data.get('linkedin_fetch_description', False)
        proxies = request.data.get('proxies', [])
        search_term = request.data.get('search_term', '')
        dry_run = request.data.get('dry_run', False)

        # Validate site_names
        valid_sites = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor', 'google', 'bayt', 'naukri']
        if not isinstance(site_names, list) or not all(site in valid_sites for site in site_names):
            return Response(
                {"error": f"Invalid site_names. Must be a list containing: {valid_sites}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate results_wanted
        if not isinstance(results_wanted, int) or results_wanted < 1 or results_wanted > 1000:
            return Response(
                {"error": "results_wanted must be an integer between 1 and 1000"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Prepare scraping parameters
        scrape_params = {
            'site_name': site_names,
            'location': location,
            'results_wanted': results_wanted,
            'hours_old': hours_old,
            'country_indeed': country_indeed,
            'verbose': 1,
            'description_format': 'markdown',
        }

        # Add optional parameters
        if search_term:
            scrape_params['search_term'] = search_term
            
        if job_type and job_type in ['fulltime', 'parttime', 'internship', 'contract']:
            scrape_params['job_type'] = job_type
        
        if is_remote:
            scrape_params['is_remote'] = True
            
        if linkedin_fetch_description:
            scrape_params['linkedin_fetch_description'] = True
            
        if proxies and isinstance(proxies, list):
            scrape_params['proxies'] = proxies

        try:
            # Scrape jobs
            jobs_df = scrape_jobs(**scrape_params)
            
            if jobs_df.empty:
                return Response({
                    'success': True,
                    'message': 'No jobs found with the given criteria',
                    'stats': {
                        'scraped_count': 0,
                        'parameters': scrape_params
                    }
                }, status=status.HTTP_200_OK)

            scraped_count = len(jobs_df)

            if dry_run:
                # Return sample data without saving
                sample_jobs = jobs_df.head(5).to_dict('records')
                return Response({
                    'success': True,
                    'message': f'DRY RUN: Found {scraped_count} jobs (showing first 5)',
                    'sample_data': sample_jobs,
                    'stats': {
                        'scraped_count': scraped_count,
                        'parameters': scrape_params
                    }
                }, status=status.HTTP_200_OK)

            # Convert DataFrame to format compatible with BulkJobCreateSerializer
            job_data = self._convert_jobspy_to_opportunities(jobs_df)
            
            # Use the existing bulk create serializer
            batch_id = f"jobspy_{uuid.uuid4().hex[:8]}"
            serializer_data = {
                'jobs': job_data,
                'batch_id': batch_id,
                'source': 'jobspy'
            }

            serializer = BulkJobCreateSerializer(
                data=serializer_data,
                context={'user': getattr(request, 'user', None)}
            )
            
            if serializer.is_valid():
                with transaction.atomic():
                    result = serializer.save()
                    
                # Clear recommendation cache for all users
                cache_pattern = 'user_recommendations_*'
                cache.delete_pattern(cache_pattern)
                
                response_data = {
                    'success': True,
                    'message': f'Successfully scraped and imported {result["created_count"]} jobs',
                    'stats': {
                        'scraped_count': scraped_count,
                        'created_count': result['created_count'],
                        'skipped_count': result['skipped_count'],
                        'error_count': result['error_count'],
                        'batch_id': result['batch_id'],
                        'parameters': scrape_params
                    }
                }
                
                if result['errors']:
                    response_data['errors'] = result['errors']
                
                response_data['created_opportunity_ids'] = [
                    opp.id for opp in result['opportunities']
                ]
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
            else:
                return Response({
                    'error': 'Data validation failed',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": f"Job scraping failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _convert_jobspy_to_opportunities(self, jobs_df):
        """Convert JobSpy DataFrame to format compatible with opportunity model"""
        job_data = []
        
        for _, job in jobs_df.iterrows():
            # Map JobSpy job types to our opportunity types
            job_type_mapping = {
                'fulltime': 'job',
                'parttime': 'job', 
                'internship': 'internship',
                'contract': 'job',
            }
            
            # Determine experience level from title and description
            experience_level = self._determine_experience_level(
                job.get('TITLE', ''), 
                job.get('DESCRIPTION', '')
            )
            
            # Parse salary information
            salary_data = self._parse_salary_info(job)
            
            # Determine source platform
            source = job.get('SITE', 'other').lower()
            if source == 'zip_recruiter':
                source = 'other'
            elif source not in ['linkedin', 'indeed', 'glassdoor']:
                source = 'other'

            opportunity_data = {
                'title': str(job.get('TITLE', '')).strip(),
                'type': job_type_mapping.get(job.get('JOB_TYPE', ''), 'job'),
                'organization': str(job.get('COMPANY', '')).strip(),
                'location': self._format_location(job),
                'is_remote': bool(job.get('is_remote', False)) or 'remote' in str(job.get('location', '')).lower(),
                'experience_level': experience_level,
                'description': str(job.get('DESCRIPTION', '')).strip(),
                'application_url': str(job.get('JOB_URL', '')).strip(),
                'source': source,
                'external_id': self._generate_external_id(job),
                **salary_data
            }
            
            # Add skills if available (Naukri specific)
            if 'skills' in job and job['skills']:
                skills = self._parse_skills(job['skills'])
                if skills:
                    opportunity_data['skills_required'] = skills

            job_data.append(opportunity_data)
            
        return job_data

    def _determine_experience_level(self, title, description):
        """Determine experience level from job title and description"""
        title_lower = title.lower()
        desc_lower = description.lower() if description else ''
        
        # Senior level indicators
        senior_keywords = [
            'senior', 'sr.', 'lead', 'principal', 'architect', 'manager', 
            'director', 'head of', 'chief', 'vp', 'vice president'
        ]
        
        # Entry level indicators  
        entry_keywords = [
            'junior', 'jr.', 'entry', 'associate', 'trainee', 'intern',
            'graduate', 'new grad', 'recent graduate', '0-2 years'
        ]
        
        # Check for senior indicators
        for keyword in senior_keywords:
            if keyword in title_lower or keyword in desc_lower:
                return 'senior'
                
        # Check for entry indicators
        for keyword in entry_keywords:
            if keyword in title_lower or keyword in desc_lower:
                return 'entry'
                
        # Default to mid-level
        return 'mid'

    def _parse_salary_info(self, job):
        """Parse salary information from JobSpy job data"""
        salary_data = {}
        
        min_amount = job.get('MIN_AMOUNT')
        max_amount = job.get('MAX_AMOUNT')
        interval = job.get('INTERVAL', 'yearly')
        
        # Convert to numbers if available
        if min_amount and str(min_amount).replace('.', '').isdigit():
            salary_data['salary_min'] = float(min_amount)
            
        if max_amount and str(max_amount).replace('.', '').isdigit():
            salary_data['salary_max'] = float(max_amount)
            
        # Map interval to our salary period choices
        interval_mapping = {
            'yearly': 'yearly',
            'monthly': 'monthly', 
            'weekly': 'weekly',
            'daily': 'daily',
            'hourly': 'hourly'
        }
        
        if interval in interval_mapping:
            salary_data['salary_period'] = interval_mapping[interval]
        else:
            salary_data['salary_period'] = 'yearly'
            
        # Default currency
        salary_data['salary_currency'] = 'USD'
        
        return salary_data

    def _format_location(self, job):
        """Format location from JobSpy job data"""
        city = job.get('CITY', '')
        state = job.get('STATE', '')
        country = job.get('country', '')
        
        # Combine location parts
        location_parts = []
        if city:
            location_parts.append(str(city).strip())
        if state:
            location_parts.append(str(state).strip())
        if country and country != 'USA':
            location_parts.append(str(country).strip())
            
        return ', '.join(location_parts) if location_parts else 'Remote'

    def _generate_external_id(self, job):
        """Generate a unique external ID for the job"""
        job_url = job.get('JOB_URL', '')
        if job_url:
            # Extract ID from URL if possible
            url_id = re.search(r'(?:jk=|jobid=|jobs/view/)([a-zA-Z0-9]+)', job_url)
            if url_id:
                return f"{job.get('SITE', 'unknown')}_{url_id.group(1)}"
        
        # Fallback to hash of title + company
        title = str(job.get('TITLE', '')).strip()
        company = str(job.get('COMPANY', '')).strip()
        return f"{job.get('SITE', 'unknown')}_{hash(title + company) % 1000000}"

    def _parse_skills(self, skills_data):
        """Parse skills from job data (mainly for Naukri)"""
        if isinstance(skills_data, str):
            # Split by common delimiters
            skills = re.split(r'[,;|]', skills_data)
            return [skill.strip() for skill in skills if skill.strip()]
        elif isinstance(skills_data, list):
            return [str(skill).strip() for skill in skills_data if str(skill).strip()]
        
        return []
