from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # API endpoints
    # Auth endpoints
    path('api/auth/google/', views.auth_receiver, name='auth_receiver'),
    path('api/auth/google-client-id/', views.get_google_client_id, name='get_google_client_id'),
    path('api/auth/sign-out/', views.sign_out, name='sign_out'),
    
    # User registration and management
    path('api/register/', views.register_user, name='register'),
    path('api/role/', views.UserRoleAPIView.as_view(), name='user_role_api'),
]
