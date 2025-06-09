from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # API endpoints
    # Auth endpoints
    path('api/auth/google/', views.exchange_code, name='google_auth'),  # API endpoint for code exchange
    path('api/auth/google/start/', views.oauth_start, name='google_oauth_start'),  # Start OAuth flow
    path('api/auth/google/callback/', views.oauth_callback, name='google_oauth_callback'),  # OAuth callback
    path('api/auth/google-client-id/', views.get_google_client_id, name='get_google_client_id'),
    path('api/auth/sign-out/', views.sign_out, name='sign_out'),
    
    # User registration and management
    path('api/register/', views.register_user, name='register'),
    path('api/role/', views.UserRoleAPIView.as_view(), name='user_role_api'),
]
