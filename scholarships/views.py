from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from .models import Scholarship, UserScholarship,ScholarshipProfile
from .serializers import ScholarshipSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from scholarships.matching.scholarship_matching import score_scholarship
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated



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

#Recommended scholarships for a user
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommended_scholarships(request):
    try:
        profile = ScholarshipProfile.objects.get(user=request.user)
    except ScholarshipProfile.DoesNotExist:
        return Response({"error": "User profile not found."}, status=404)

    results = []
    for scholarship in Scholarship.objects.all():
        score = score_scholarship(profile, scholarship)
        results.append((score, scholarship))

    results.sort(key=lambda x: x[0], reverse=True)

    serialized_data = []
    for score, scholarship in results:
        serialized = ScholarshipSerializer(scholarship).data
        serialized['match_score'] = score
        serialized_data.append(serialized)

    return Response(serialized_data)