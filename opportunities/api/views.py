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


    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recommended(self, request):
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


