from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SendOTPView, VerifyOTPView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('', include(router.urls)),
]