from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from django.core.cache import cache
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
import hashlib
import json
from .serializers import OpportunitySerializer, OpportunityRecommendationSerializer
from opportunities.matching import OpportunityMatcher
from opportunities.models import Opportunity


class OpportunityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OpportunityViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing opportunities
    """
    serializer_class = OpportunitySerializer
    permission_classes = [AllowAny]
    pagination_class = OpportunityPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'location', 'is_remote', 'category__slug', 'tags__slug', 'deadline']
    search_fields = ['title', 'description', 'organization']
    ordering_fields = ['deadline', 'created_at', 'title', 'view_count']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Opportunity.objects.all()

        # Full-text search (Postgres)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            query = SearchQuery(search_query)
            queryset = queryset.annotate(rank=SearchRank(F('search_vector'), query)) \
                               .filter(search_vector=query) \
                               .order_by('-rank')

        # Filter by skills (skills_required is assumed to be a JSONField or ArrayField)
        skills = self.request.query_params.getlist('skills', None)
        if skills:
            for skill in skills:
                queryset = queryset.filter(skills_required__contains=[skill])

        # Show only future deadlines unless explicitly showing expired
        show_expired = self.request.query_params.get('show_expired', 'false').lower()
        if show_expired != 'true':
            queryset = queryset.filter(deadline__gte=timezone.now().date())

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
        """
        Returns personalized recommendations based on user profile and preferences,
        supports caching, ordering, and pagination.
        """
        user_profile = request.user.profile

        # Extract filters from query params
        filters = {}
        for param in ['type', 'location', 'category']:
            val = request.query_params.get(param)
            if val:
                filters[param] = val

        tags = request.query_params.getlist('tags')
        if tags:
            filters['tags'] = tags

        skills = request.query_params.getlist('skills')
        if skills:
            filters['skills'] = skills

        deadline_after = request.query_params.get('deadline_after')
        if deadline_after:
            filters['deadline_after'] = deadline_after

        deadline_before = request.query_params.get('deadline_before')
        if deadline_before:
            filters['deadline_before'] = deadline_before

        # Ordering param for recommended results, default by score descending
        ordering = request.query_params.get('ordering', '-score')

        # Build cache key based on user id, filters and ordering
        cache_key_raw = {
            'user_id': request.user.id,
            'filters': filters,
            'ordering': ordering
        }
        cache_key = 'recommendations_' + hashlib.md5(json.dumps(cache_key_raw, sort_keys=True).encode()).hexdigest()

        cached_data = cache.get(cache_key)
        if cached_data:
            return self.get_paginated_response(cached_data)

        # Get recommendations from matcher
        matcher = OpportunityMatcher(user_profile)
        recommendations = matcher.get_recommended_opportunities(filters=filters)

        # Allowed fields for ordering in recommendations
        allowed_order_fields = {'score', 'deadline', 'title'}
        reverse = ordering.startswith('-')
        order_field = ordering.lstrip('-')

        if order_field not in allowed_order_fields:
            order_field = 'score'  # default ordering

        # Sort recommendations (list of dicts or objects with attributes)
        recommendations = sorted(
            recommendations,
            key=lambda rec: rec.get(order_field) if isinstance(rec, dict) else getattr(rec, order_field, None),
            reverse=reverse
        )

        # Paginate
        page = self.paginate_queryset(recommendations)
        if page is not None:
            serializer = OpportunityRecommendationSerializer(page, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=300)  # cache for 5 minutes
            return self.get_paginated_response(data)

        serializer = OpportunityRecommendationSerializer(recommendations, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=300)
        return Response(data)

    @action(detail=True, methods=['post'])
    def track_view(self, request, pk=None):
        """Track that a user viewed an opportunity"""
        opportunity = self.get_object()
        opportunity.view_count = F('view_count') + 1
        opportunity.save(update_fields=['view_count'])
        opportunity.refresh_from_db(fields=['view_count'])
        return Response({'status': 'view tracked', 'view_count': opportunity.view_count})

    @action(detail=True, methods=['post'])
    def track_application(self, request, pk=None):
        """Track that a user applied to an opportunity"""
        opportunity = self.get_object()
        opportunity.application_count = F('application_count') + 1
        opportunity.save(update_fields=['application_count'])
        opportunity.refresh_from_db(fields=['application_count'])
        return Response({'status': 'application tracked', 'application_count': opportunity.application_count})
