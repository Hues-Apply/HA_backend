from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # API endpoints
    # Auth endpoints - New OAuth 2.0 flow
    path('api/auth/google/callback/', views.GoogleAuthCallbackView.as_view(), name='google-auth-callback'),  # Main OAuth callback
    path('api/auth/google/refresh-token/', views.google_refresh_token, name='google-refresh-token'),  # Refresh Google tokens
    path('api/auth/google-client-id/', views.GoogleClientIDView.as_view(), name='google-client-id'),  # Client ID endpoint
    
    path('api/auth/sign-out/', views.sign_out, name='sign_out'),
    
    # User registration and management
    path('api/register/', views.register_user, name='register'),
    path('api/role/', views.UserRoleAPIView.as_view(), name='user_role_api'),
]
