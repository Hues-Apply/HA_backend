from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Document, ParsedProfile, ProjectsProfile, UserGoal, CustomUser
from .serializers import (
    DocumentSerializer, EducationProfileSerializer, ParsedProfileSerializer,
    ProfileCompletionSerializer, ProjectsProfileSerializer, UserGoalUpdateSerializer, UserGoalSerializer
)


# Temporary endpoints for user management
@api_view(['GET'])
@permission_classes([AllowAny])  # No authentication required for temporary endpoint
def google_signups_list(request):
    """Get list of all users who signed up via Google OAuth - Temporary endpoint"""
    try:
        # Get users who have Google profile data
        users = CustomUser.objects.filter(
            profile__google_id__isnull=False
        ).select_related('profile').order_by('-date_joined')

        results = []
        for user in users:
            # Check if user is new (joined in last 24 hours)
            is_new_user = (timezone.now() - user.date_joined).days < 1

            google_data = {}
            if hasattr(user, 'profile') and user.profile:
                google_data = {
                    'name': user.profile.name or f"{user.first_name} {user.last_name}".strip(),
                    'picture': user.profile.google_picture or ''
                }

            results.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.get_role(),
                'is_new_user': is_new_user,
                'created_at': user.date_joined.isoformat(),
                'google_data': google_data
            })

        return Response({
            'count': len(results),
            'results': results
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to retrieve users: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])  # No authentication required for temporary endpoint
def delete_user(request, user_id):
    """Delete a specific user by ID - Temporary endpoint"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        user_email = user.email
        user.delete()

        return Response({
            'message': f'User {user_email} deleted successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to delete user: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentUploadView(APIView):
    """Upload CV/Resume documents - File upload only"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            # Create document instance
            serializer = DocumentSerializer(data=request.data)
            if serializer.is_valid():
                document = serializer.save(user=request.user)

                # Set status to uploaded (parsing will be done on frontend)
                document.processing_status = 'uploaded'
                document.save()

                return Response({
                    'success': True,
                    'document_id': str(document.id),
                    'message': 'Document uploaded successfully. Please send parsed data to complete profile.'
                }, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': f'Document upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_parsed_profile(request):
    """Update parsed profile data from frontend parsing"""
    try:
        data = request.data

        # Get the document if document_id is provided
        document = None
        if 'document_id' in data:
            try:
                document = Document.objects.get(id=data['document_id'], user=request.user)
            except Document.DoesNotExist:
                return Response({
                    'error': 'Document not found or does not belong to user'
                }, status=status.HTTP_404_NOT_FOUND)

        # Create or update parsed profile
        parsed_profile, created = ParsedProfile.objects.get_or_create(
            user=request.user,
            defaults={'document': document}
        )

        # If updating existing profile, update document reference if provided
        if not created and document:
            parsed_profile.document = document

        # Update parsed profile with data from frontend
        update_fields = [
            'first_name', 'last_name', 'email', 'phone', 'address',
            'linkedin', 'portfolio', 'summary', 'education', 'experience',
            'skills', 'certifications', 'languages', 'projects'
        ]

        for field in update_fields:
            if field in data:
                setattr(parsed_profile, field, data[field])

        # Set confidence score if provided, otherwise default
        parsed_profile.confidence_score = data.get('confidence_score', 0.90)

        # Save the profile
        parsed_profile.save()

        # Update document status to completed if document exists
        if document:
            document.processing_status = 'completed'
            document.processed_at = timezone.now()
            document.save()

        # Return the saved profile data
        serializer = ParsedProfileSerializer(parsed_profile)
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'profile_data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Profile update failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_completion_status(request):
    """Get profile completion status"""
    try:
        parsed_profile = ParsedProfile.objects.get(user=request.user)

        completion_data = {
            'completion_percentage': parsed_profile.completion_percentage,
            'missing_sections': parsed_profile.missing_sections,
            'completed_sections': parsed_profile.completed_sections
        }

        serializer = ProfileCompletionSerializer(completion_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except ParsedProfile.DoesNotExist:
        # No profile exists yet
        return Response({
            'completion_percentage': 0,
            'missing_sections': ['personal_info', 'summary', 'education', 'experience', 'skills'],
            'completed_sections': []
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': f'Status check failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_goals(request):
    """Update user goals"""
    try:
        serializer = UserGoalUpdateSerializer(data=request.data)
        if serializer.is_valid():
            goals_data = serializer.validated_data['goals']

            with transaction.atomic():
                # Remove existing goals
                UserGoal.objects.filter(user=request.user).delete()

                # Create new goals
                new_goals = []
                for i, goal in enumerate(goals_data, 1):
                    new_goals.append(UserGoal(
                        user=request.user,
                        goal=goal,
                        priority=i
                    ))

                UserGoal.objects.bulk_create(new_goals)

            return Response({'success': True}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Goals update failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_goals(request):
    """Get user's current goals"""
    try:
        goals = UserGoal.objects.filter(user=request.user).order_by('priority')
        serializer = UserGoalSerializer(goals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Goals retrieval failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_parsed_profile(request):
    """Get current user's parsed profile data"""
    try:
        parsed_profile = ParsedProfile.objects.get(user=request.user)
        serializer = ParsedProfileSerializer(parsed_profile)
        return Response({
            'success': True,
            'profile_data': serializer.data
        }, status=status.HTTP_200_OK)

    except ParsedProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No parsed profile found. Please upload a document and send parsed data.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Profile retrieval failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_comprehensive_user_profile(request):
    """Get comprehensive user profile data in a single request"""
    try:
        from .serializers import ComprehensiveUserProfileSerializer

        serializer = ComprehensiveUserProfileSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to retrieve user profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Profile Management Endpoints for Individual Sections

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_education_profile(request):
    """Create a new education entry"""
    try:
        serializer = EducationProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Failed to create education profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_experience_profile(request):
    """Create a new experience entry"""
    from .serializers import ExperienceProfileSerializer
    try:
        serializer = ExperienceProfileSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'error': f'Failed to create experience profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_project_profile(request):
#     """Create a new project entry"""
#     try:
#         from .serializers import ProjectsProfileSerializer

#         serializer = ProjectsProfileSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({
#                 'success': True,
#                 'data': serializer.data
#             }, status=status.HTTP_201_CREATED)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     except Exception as e:
#         return Response({
#             'error': f'Failed to create project profile: {str(e)}'
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project_profile(request):
    """Create a new project entry"""
    try:
        serializer = ProjectsProfileSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

        # ✅ Print exact field-level errors to terminal
        print("❌ Serializer errors:", serializer.errors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return Response({
            'error': f'Failed to create project profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def project_detail_view(request, pk):
    try:
        project = ProjectsProfile.objects.get(pk=pk, user=request.user)
    except ProjectsProfile.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = ProjectsProfileSerializer(project, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        project.delete()
        return Response({'success': True, 'message': 'Project deleted'})

@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def manage_career_profile(request):
    """Create or get career profile"""
    try:
        from .models import CareerProfile
        from .serializers import CareerProfileSerializer

        if request.method == 'GET':
            try:
                career_profile = CareerProfile.objects.get(user=request.user)
                serializer = CareerProfileSerializer(career_profile)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except CareerProfile.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No career profile found'
                }, status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'POST':
            career_profile, created = CareerProfile.objects.get_or_create(
                user=request.user,
                defaults=request.data
            )

            if not created:
                # Update existing profile
                for field, value in request.data.items():
                    if hasattr(career_profile, field):
                        setattr(career_profile, field, value)
                career_profile.save()

            serializer = CareerProfileSerializer(career_profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to manage career profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def manage_opportunities_interest(request):
    """Create or update opportunities interest"""
    try:
        from .models import OpportunitiesInterest
        from .serializers import OpportunitiesInterestSerializer

        if request.method == 'GET':
            try:
                interest = OpportunitiesInterest.objects.get(user=request.user)
                serializer = OpportunitiesInterestSerializer(interest)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except OpportunitiesInterest.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No opportunities interest found'
                }, status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'POST':
            interest, created = OpportunitiesInterest.objects.get_or_create(
                user=request.user,
                defaults=request.data
            )

            if not created:
                # Update existing
                for field, value in request.data.items():
                    if hasattr(interest, field):
                        setattr(interest, field, value)
                interest.save()

            serializer = OpportunitiesInterestSerializer(interest)
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to manage opportunities interest: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def manage_recommendation_priority(request):
    """Create or update recommendation priority"""
    try:
        from .models import RecommendationPriority
        from .serializers import RecommendationPrioritySerializer

        if request.method == 'GET':
            try:
                priority = RecommendationPriority.objects.get(user=request.user)
                serializer = RecommendationPrioritySerializer(priority)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except RecommendationPriority.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No recommendation priority found'
                }, status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'POST':
            priority, created = RecommendationPriority.objects.get_or_create(
                user=request.user,
                defaults=request.data
            )

            if not created:
                # Update existing
                for field, value in request.data.items():
                    if hasattr(priority, field):
                        setattr(priority, field, value)
                priority.save()

            serializer = RecommendationPrioritySerializer(priority)
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to manage recommendation priority: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def manage_personal_profile(request):
    """Create or update personal profile information"""
    try:
        from .models import UserProfile
        from .serializers import UserProfileSerializer

        if request.method == 'GET':
            # Get existing profile or return empty data
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = UserProfileSerializer(profile)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except UserProfile.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'No profile found'
                }, status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'POST':
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(
                user=request.user,
                defaults={}
            )

            # Update profile fields
            update_fields = ['name', 'email', 'phone_number', 'country', 'goal']
            for field in update_fields:
                if field in request.data:
                    setattr(profile, field, request.data[field])

            # Handle CV upload if present
            if 'cv_file' in request.FILES:
                uploaded_file = request.FILES['cv_file']
                profile.cv_file = uploaded_file.read()
                profile.cv_filename = uploaded_file.name
                profile.cv_mime = uploaded_file.content_type

            # Also update user's basic info
            if 'first_name' in request.data:
                request.user.first_name = request.data['first_name']
            if 'last_name' in request.data:
                request.user.last_name = request.data['last_name']
            if 'email' in request.data:
                request.user.email = request.data['email']
            if 'country' in request.data:
                request.user.country = request.data['country']

            request.user.save()
            profile.save()

            serializer = UserProfileSerializer(profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Failed to manage personal profile: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
