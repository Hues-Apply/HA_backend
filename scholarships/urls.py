from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScholarshipViewSet, recommended_scholarships


router = DefaultRouter()
router.register(r'', ScholarshipViewSet, basename='scholarship')

urlpatterns = [
    path('match/', recommended_scholarships, name='match-scholarships'),  
    path('', include(router.urls)),
]
