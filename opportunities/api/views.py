from rest_framework import viewsets, filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from .serializers import OpportunitySerializer
from opportunities.models import Opportunity
from django.utils import timezone


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
        
        # Handle full-text search for better results
        search_query = self.request.query_params.get('search', None)
        if search_query:
            query = SearchQuery(search_query)
            queryset = queryset.annotate(
                rank=SearchRank(F('search_vector'), query)
            ).filter(search_vector=query).order_by('-rank')
        
        # Filter by skills
        skills = self.request.query_params.getlist('skills', None)
        if skills:
            for skill in skills:
                queryset = queryset.filter(skills_required__contains=[skill])
        
        # Show only opportunities with future deadlines by default
        if not self.request.query_params.get('show_expired', False):
            queryset = queryset.filter(deadline__gte=timezone.now().date())
        
        return queryset
   