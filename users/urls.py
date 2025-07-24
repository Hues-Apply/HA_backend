from django.urls import path
from . import views
from . import profile_views

app_name = 'users'

urlpatterns = [
    # API endpoints
    # Auth endpoints - New OAuth 2.0 flow
    path('api/auth/google/callback/', views.GoogleAuthCallbackView.as_view(), name='google-auth-callback'),  # Main OAuth callback
    path('api/auth/google/', views.GoogleCredentialAuthView.as_view(), name='google-credential-auth'),  # Credential-based Google auth
    path('api/auth/google/refresh-token/', views.google_refresh_token, name='google-refresh-token'),  # Refresh Google tokens
    path('api/auth/google-client-id/', views.GoogleClientIDView.as_view(), name='google-client-id'),  # Client ID endpoint
    
    path('api/auth/sign-out/', views.sign_out, name='sign_out'),
    
    # User registration and management
    path('api/register/', views.register_user, name='register'),
    path('api/role/', views.UserRoleAPIView.as_view(), name='user_role_api'),
      # Temporary user management endpoints
    path('api/users/google-signups/', profile_views.google_signups_list, name='google-signups-list'),
    path('api/users/<int:user_id>/delete/', profile_views.delete_user, name='delete-user'),
    
    # Profile Management endpoints
    path('api/profile/upload-document-file/', profile_views.DocumentUploadView.as_view(), name='upload-document-file'),
    path('api/profile/update-parsed/', profile_views.update_parsed_profile, name='update-parsed-profile'),
    path('api/profile/get-parsed/', profile_views.get_parsed_profile, name='get-parsed-profile'),
    path('api/profile/comprehensive/', profile_views.get_comprehensive_user_profile, name='get-comprehensive-profile'),
    path('api/profile/completion-status/', profile_views.profile_completion_status, name='profile-completion-status'),
    path('api/profile/update-goals/', profile_views.update_user_goals, name='update-user-goals'),
    path('api/profile/goals/', profile_views.get_user_goals, name='get-user-goals'),
    
    # Personal profile management
    path('api/profile/personal/', profile_views.manage_personal_profile, name='manage-personal-profile'),
    
    # Individual Profile Section Management
    path('api/profile/education/', profile_views.create_education_profile, name='create-education-profile'),
    path('api/profile/experience/', profile_views.create_experience_profile, name='create-experience-profile'),
    path('api/profile/project/', profile_views.create_project_profile, name='create-project-profile'),
    path('profile/project/<int:pk>/', profile_views.project_detail_view),
    path('api/profile/career/', profile_views.manage_career_profile, name='manage-career-profile'),
    path('api/profile/opportunities-interest/', profile_views.manage_opportunities_interest, name='manage-opportunities-interest'),
    path('api/profile/recommendation-priority/', profile_views.manage_recommendation_priority, name='manage-recommendation-priority'),
    path('api/profile/scholarship/', profile_views.manage_scholarship_profile, name='manage-scholarship-profile'),
]
