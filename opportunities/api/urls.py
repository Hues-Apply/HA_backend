from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OpportunityViewSet, UserOpportunityApplicationsView

router = DefaultRouter()
router.register(r'', OpportunityViewSet, basename='opportunity')

urlpatterns = [
    path('', include(router.urls)),
    path('applications/', UserOpportunityApplicationsView.as_view(), name='user-opportunity-applications'),
    ]
