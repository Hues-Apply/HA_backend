from rest_framework import viewsets, filters, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from .models import Job, UserJob
from .serializers import JobSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

class JobPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [AllowAny]
    pagination_class = JobPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'job_type', 'experience_level', 'skills']
    search_fields = ['title', 'company', 'location', 'skills', 'experience_level']
    ordering_fields = ['posted_at', 'title']
    ordering = ['-posted_at']

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
            "message": "Job updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='apply', permission_classes=[AllowAny])
    def apply(self, request, pk=None):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        job = get_object_or_404(Job, pk=pk)
        user_job, created = UserJob.objects.get_or_create(
            user=request.user, job=job,
            defaults={'applied': True}
        )
        if not created and not user_job.applied:
            user_job.applied = True
            user_job.save()
        return Response({'success': True, 'applied': True, 'application_id': user_job.id})

    @action(detail=False, methods=['get'], url_path='applications')
    def applications(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
        user_jobs = UserJob.objects.filter(user=request.user)
        data = [
            {
                'id': uj.id,
                'job_id': uj.job.id,
                'applied': uj.applied,
                'applied_date': uj.applied_date,
                'updated_at': uj.updated_at,
            }
            for uj in user_jobs
        ]
        return Response({'applications': data})


