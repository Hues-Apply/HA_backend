from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from .models import Scholarship, UserScholarship
from .serializers import ScholarshipSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class ScholarshipPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ScholarshipViewSet(viewsets.ModelViewSet):
    queryset = Scholarship.objects.all()
    serializer_class = ScholarshipSerializer
    permission_classes = [AllowAny]
    pagination_class = ScholarshipPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'source', 'location', 'course', 'gpa', 'deadline'
    ]
    search_fields = ['title', 'amount', 'location', 'course', 'source']
    ordering_fields = ['deadline', 'scraped_at', 'title']
    ordering = ['-scraped_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        exclude_id = self.request.query_params.get('exclude')
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "message": "Scholarship updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Scholarship deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post'], url_path='apply', permission_classes=[AllowAny])
    def apply(self, request, pk=None):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        scholarship = get_object_or_404(Scholarship, pk=pk)
        user_sch, created = UserScholarship.objects.get_or_create(
            user=request.user, scholarship=scholarship,
            defaults={'applied': True}
        )
        if not created and not user_sch.applied:
            user_sch.applied = True
            user_sch.save()
        return Response({'success': True, 'applied': True, 'application_id': user_sch.id})

    @action(detail=False, methods=['get'], url_path='applications')
    def applications(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        user_scholarships = UserScholarship.objects.filter(user=request.user)
        data = [
            {
                'id': us.id,
                'scholarship_id': us.scholarship.id,
                'applied': us.applied,
                'applied_date': us.applied_date,
                'updated_at': us.updated_at,
            }
            for us in user_scholarships
        ]
        return Response({'applications': data})
