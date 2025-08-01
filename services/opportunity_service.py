"""
Service layer for opportunity-related business logic.
This separates business logic from views and provides reusable functionality.
"""
import logging
from typing import List, Dict, Optional, Tuple
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError

from opportunities.models import Opportunity, OpportunityApplication, Category, Tag
from users.models import UserProfile
from config.constants import MATCHING_WEIGHTS, CACHE_TIMEOUT, RECOMMENDATION_CACHE_TIMEOUT
from utils.response_utils import sanitize_input

logger = logging.getLogger(__name__)

class OpportunityService:
    """Service class for opportunity-related operations."""

    @staticmethod
    def create_opportunity(data: Dict, user=None) -> Opportunity:
        """Create a new opportunity with validation."""
        try:
            with transaction.atomic():
                # Sanitize input data
                sanitized_data = {
                    'title': sanitize_input(data.get('title', ''), 255),
                    'type': data.get('type'),
                    'organization': sanitize_input(data.get('organization', ''), 255),
                    'location': sanitize_input(data.get('location', ''), 100),
                    'description': sanitize_input(data.get('description', ''), 5000),
                    'deadline': data.get('deadline'),
                    'is_remote': data.get('is_remote', False),
                    'experience_level': data.get('experience_level', 'entry'),
                    'salary_min': data.get('salary_min'),
                    'salary_max': data.get('salary_max'),
                    'salary_currency': data.get('salary_currency', 'USD'),
                    'application_url': data.get('application_url', ''),
                    'skills_required': data.get('skills_required', []),
                }

                # Validate required fields
                required_fields = ['title', 'type', 'organization', 'deadline']
                for field in required_fields:
                    if not sanitized_data.get(field):
                        raise ValidationError(f"Field '{field}' is required")

                # Get or create category
                category_name = data.get('category', 'General')
                category, _ = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Category for {category_name}'}
                )
                sanitized_data['category'] = category

                # Create opportunity
                opportunity = Opportunity.objects.create(**sanitized_data)

                # Handle tags
                tags = data.get('tags', [])
                if tags:
                    tag_objects = []
                    for tag_name in tags:
                        tag, _ = Tag.objects.get_or_create(
                            name=sanitize_input(tag_name, 50),
                            defaults={'slug': tag_name.lower().replace(' ', '-')}
                        )
                        tag_objects.append(tag)
                    opportunity.tags.set(tag_objects)

                logger.info(f"Created opportunity: {opportunity.title}")
                return opportunity

        except Exception as e:
            logger.error(f"Error creating opportunity: {str(e)}")
            raise

    @staticmethod
    def update_opportunity(opportunity_id: int, data: Dict, user=None) -> Opportunity:
        """Update an existing opportunity."""
        try:
            with transaction.atomic():
                opportunity = Opportunity.objects.get(id=opportunity_id)

                # Update fields
                for field, value in data.items():
                    if hasattr(opportunity, field) and field not in ['id', 'created_at']:
                        if isinstance(value, str):
                            value = sanitize_input(value)
                        setattr(opportunity, field, value)

                opportunity.save()
                logger.info(f"Updated opportunity: {opportunity.title}")
                return opportunity

        except Opportunity.DoesNotExist:
            raise ValidationError("Opportunity not found")
        except Exception as e:
            logger.error(f"Error updating opportunity: {str(e)}")
            raise

    @staticmethod
    def delete_opportunity(opportunity_id: int, user=None) -> bool:
        """Delete an opportunity."""
        try:
            opportunity = Opportunity.objects.get(id=opportunity_id)
            opportunity.delete()
            logger.info(f"Deleted opportunity: {opportunity_id}")
            return True
        except Opportunity.DoesNotExist:
            raise ValidationError("Opportunity not found")
        except Exception as e:
            logger.error(f"Error deleting opportunity: {str(e)}")
            raise

    @staticmethod
    def get_opportunity(opportunity_id: int) -> Optional[Opportunity]:
        """Get a single opportunity by ID."""
        try:
            return Opportunity.objects.select_related('category').prefetch_related('tags').get(id=opportunity_id)
        except Opportunity.DoesNotExist:
            return None

    @staticmethod
    def search_opportunities(
        query: str = None,
        opportunity_type: str = None,
        location: str = None,
        experience_level: str = None,
        is_remote: bool = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """Search opportunities with filters and pagination."""
        try:
            queryset = Opportunity.objects.select_related('category').prefetch_related('tags')

            # Apply filters
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) |
                    Q(description__icontains=query) |
                    Q(organization__icontains=query) |
                    Q(skills_required__icontains=query)
                )

            if opportunity_type:
                queryset = queryset.filter(type=opportunity_type)

            if location:
                queryset = queryset.filter(location__icontains=location)

            if experience_level:
                queryset = queryset.filter(experience_level=experience_level)

            if is_remote is not None:
                queryset = queryset.filter(is_remote=is_remote)

            # Filter by active opportunities and future deadlines
            queryset = queryset.filter(
                is_active=True,
                deadline__gte=timezone.now().date()
            ).order_by('-created_at')

            # Paginate results
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            return {
                'results': page_obj.object_list,
                'pagination': {
                    'count': paginator.count,
                    'next': page_obj.has_next(),
                    'previous': page_obj.has_previous(),
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'page_size': page_size,
                }
            }

        except Exception as e:
            logger.error(f"Error searching opportunities: {str(e)}")
            raise

    @staticmethod
    def get_recommendations_for_user(user_profile: UserProfile, limit: int = 10) -> List[Opportunity]:
        """Get personalized opportunity recommendations for a user."""
        cache_key = f'user_recommendations_{user_profile.user.id}'
        cached_result = cache.get(cache_key)

        if cached_result:
            return cached_result[:limit]

        try:
            # Get user preferences and skills
            user_skills = user_profile.skills or []
            user_location = user_profile.location
            user_education = user_profile.education_level

            # Get opportunities
            opportunities = Opportunity.objects.filter(
                deadline__gte=timezone.now().date(),
                is_active=True
            ).prefetch_related('tags')

            # Score opportunities
            scored_opportunities = []
            for opportunity in opportunities:
                score = OpportunityService._calculate_match_score(
                    opportunity, user_skills, user_location, user_education
                )
                if score > 0.1:  # Only include relevant opportunities
                    scored_opportunities.append((opportunity, score))

            # Sort by score and get top results
            scored_opportunities.sort(key=lambda x: x[1], reverse=True)
            recommendations = [opp for opp, score in scored_opportunities[:limit]]

            # Cache results
            cache.set(cache_key, recommendations, RECOMMENDATION_CACHE_TIMEOUT)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []

    @staticmethod
    def _calculate_match_score(
        opportunity: Opportunity,
        user_skills: List[str],
        user_location: str,
        user_education: str
    ) -> float:
        """Calculate match score between opportunity and user profile."""
        total_score = 0.0

        # Skills match
        if user_skills and opportunity.skills_required:
            skills_match = len(set(user_skills) & set(opportunity.skills_required))
            skills_score = skills_match / len(opportunity.skills_required) if opportunity.skills_required else 0
            total_score += skills_score * MATCHING_WEIGHTS['skills_match']

        # Location match
        if user_location and opportunity.location:
            location_match = user_location.lower() in opportunity.location.lower()
            total_score += (1.0 if location_match else 0.0) * MATCHING_WEIGHTS['location_match']

        # Education match (simplified)
        if user_education and opportunity.experience_level:
            education_score = 0.5  # Placeholder for education matching logic
            total_score += education_score * MATCHING_WEIGHTS['education_match']

        return total_score

    @staticmethod
    def apply_to_opportunity(user, opportunity_id: int) -> bool:
        """Apply user to an opportunity."""
        try:
            with transaction.atomic():
                opportunity = Opportunity.objects.get(id=opportunity_id)

                # Check if already applied
                if OpportunityApplication.objects.filter(user=user, opportunity=opportunity).exists():
                    raise ValidationError("Already applied to this opportunity")

                # Create application
                application = OpportunityApplication.objects.create(
                    user=user,
                    opportunity=opportunity
                )

                # Update opportunity application count
                opportunity.application_count = F('application_count') + 1
                opportunity.save()

                logger.info(f"User {user.email} applied to opportunity {opportunity.title}")
                return True

        except Opportunity.DoesNotExist:
            raise ValidationError("Opportunity not found")
        except Exception as e:
            logger.error(f"Error applying to opportunity: {str(e)}")
            raise

    @staticmethod
    def get_user_applications(user, page: int = 1, page_size: int = 20) -> Dict:
        """Get user's opportunity applications."""
        try:
            applications = OpportunityApplication.objects.filter(
                user=user
            ).select_related('opportunity').order_by('-applied_at')

            paginator = Paginator(applications, page_size)
            page_obj = paginator.get_page(page)

            return {
                'results': page_obj.object_list,
                'pagination': {
                    'count': paginator.count,
                    'next': page_obj.has_next(),
                    'previous': page_obj.has_previous(),
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'page_size': page_size,
                }
            }
