from rest_framework import serializers
from .models import (
    CustomUser, UserProfile, CareerProfile, EducationProfile, ExperienceProfile,
    Document, ParsedProfile, UserGoal, ProjectsProfile, OpportunitiesInterest, RecommendationPriority
)

class UserProfileSerializer(serializers.ModelSerializer):
    has_cv_in_gcs = serializers.SerializerMethodField()
    cv_download_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'name', 'email', 'profile_picture', 'phone_number', 'country', 'goal',
            'cv_gcs_path', 'cv_public_url', 'cv_filename', 'cv_mime', 'cv_uploaded_at',
            'has_cv_in_gcs', 'cv_download_url',
            'cv_file'  # Legacy field
        ]
        read_only_fields = ['cv_gcs_path', 'cv_public_url', 'cv_uploaded_at', 'has_cv_in_gcs', 'cv_download_url']

    def get_has_cv_in_gcs(self, obj):
        return obj.has_cv_in_gcs()

    def get_cv_download_url(self, obj):
        return obj.get_cv_download_url()


class CareerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerProfile
        fields = ['industry', 'job_title', 'profile_summary']

class EducationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationProfile
        fields = [
            'id', 'degree', 'school', 'start_date', 'end_date',
            'is_currently_studying', 'extra_curricular', 'created_at', 'user'
        ]
        read_only_fields = ['id', 'created_at', 'user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ExperienceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceProfile
        fields = [
            'id', 'job_title', 'company_name', 'location',
            'start_date', 'end_date', 'is_currently_working',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProjectsProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProjectsProfile
        fields = ['id', 'project_title', 'start_date', 'end_date', 'is_currently_working', 'project_link', 'description', 'created_at','user']
        read_only_fields = ['id', 'created_at']


class OpportunitiesInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunitiesInterest
        fields = ['scholarships', 'jobs', 'grants', 'internships']


class RecommendationPrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationPriority
        fields = ['academic_background', 'work_experience', 'preferred_locations', 'others', 'additional_preferences']


class CustomUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'country',
                  'is_email_verified', 'date_joined', 'role', 'profile']
        read_only_fields = ['date_joined', 'is_email_verified']

    def get_role(self, obj):
        return obj.get_role()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['applicant', 'employer'], write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name', 'country', 'role']

    def create(self, validated_data):
        role = validated_data.pop('role')
        user = CustomUser.objects.create_user(**validated_data)

        # Set role
        if role == 'applicant':
            user.set_as_applicant()
        elif role == 'employer':
            user.set_as_employer()

        return user


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document uploads"""
    download_url = serializers.SerializerMethodField()
    is_stored_in_gcs = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'original_filename', 'file_size', 'content_type',
            'gcs_path', 'gcs_public_url', 'gcs_bucket_name', 'download_url', 'is_stored_in_gcs',
            'processing_status', 'uploaded_at', 'processed_at', 'error_message',
            'file'  # Legacy field
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'processed_at', 'processing_status', 'error_message',
            'original_filename', 'gcs_path', 'gcs_public_url', 'gcs_bucket_name',
            'file_size', 'content_type', 'download_url', 'is_stored_in_gcs'
        ]

    def get_download_url(self, obj):
        return obj.get_download_url()

    def get_is_stored_in_gcs(self, obj):
        return obj.is_stored_in_gcs()

    def to_internal_value(self, data):
        # Handle different field names for file upload
        # If 'document' is provided instead of 'file', map it
        if 'document' in data and 'file' not in data:
            data = data.copy()  # Make a mutable copy
            data['file'] = data['document']
        return super().to_internal_value(data)

    def create(self, validated_data):
        # Extract original filename from uploaded file
        file = validated_data['file']
        validated_data['original_filename'] = file.name
        return super().create(validated_data)


class UserGoalSerializer(serializers.ModelSerializer):
    """Serializer for User Goals"""
    goal_display = serializers.CharField(source='get_goal_display', read_only=True)

    class Meta:
        model = UserGoal
        fields = ['id', 'goal', 'goal_display', 'priority', 'created_at']
        read_only_fields = ['id', 'created_at']


class ParsedProfileSerializer(serializers.ModelSerializer):
    """Serializer for Parsed Profile data"""
    completion_percentage = serializers.ReadOnlyField()
    missing_sections = serializers.ReadOnlyField()
    completed_sections = serializers.ReadOnlyField()
    document_info = DocumentSerializer(source='document', read_only=True)

    class Meta:
        model = ParsedProfile
        fields = [
            'user', 'document_info', 'first_name', 'last_name', 'email', 'phone',
            'address', 'linkedin', 'portfolio', 'summary', 'education', 'experience',
            'skills', 'certifications', 'languages', 'projects', 'confidence_score',
            'completion_percentage', 'missing_sections', 'completed_sections',
            'parsed_at', 'updated_at'
        ]
        read_only_fields = ['user', 'parsed_at', 'updated_at', 'completion_percentage',
                           'missing_sections', 'completed_sections']


class ProfileCompletionSerializer(serializers.Serializer):
    """Serializer for profile completion status"""
    completion_percentage = serializers.IntegerField()
    missing_sections = serializers.ListField(child=serializers.CharField())
    completed_sections = serializers.ListField(child=serializers.CharField())


class UserGoalUpdateSerializer(serializers.Serializer):
    """Serializer for updating user goals"""
    goals = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )

    def validate_goals(self, value):
        """Validate and convert goals (accepts both keys and display values)"""
        # Create mapping from display values to keys
        display_to_key = {display: key for key, display in UserGoal.GOAL_CHOICES}
        key_to_display = {key: display for key, display in UserGoal.GOAL_CHOICES}

        validated_goals = []
        for goal in value:
            # If it's already a valid key, use it
            if goal in key_to_display:
                validated_goals.append(goal)
            # If it's a display value, convert to key
            elif goal in display_to_key:
                validated_goals.append(display_to_key[goal])
            else:
                # Invalid goal
                valid_choices = list(key_to_display.keys()) + list(display_to_key.keys())
                raise serializers.ValidationError(
                    f"'{goal}' is not a valid choice. Valid choices are: {valid_choices}"
                )

        # Ensure goals are unique
        if len(validated_goals) != len(set(validated_goals)):
            raise serializers.ValidationError("Goals must be unique")

        return validated_goals

class ComprehensiveUserProfileSerializer(serializers.ModelSerializer):
    """Comprehensive serializer that returns all user profile data in one response"""

    # Personal Info from UserProfile
    profile_picture = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    goal = serializers.SerializerMethodField()

    # CV Information from UserProfile
    cv_filename = serializers.SerializerMethodField()
    cv_uploaded_at = serializers.SerializerMethodField()
    has_cv_in_gcs = serializers.SerializerMethodField()
    cv_download_url = serializers.SerializerMethodField()

    # Career Profile
    career_profile = serializers.SerializerMethodField()

    # Multiple Education entries
    education_profiles = EducationProfileSerializer(many=True, read_only=True)

    # Multiple Experience entries
    experience_profiles = ExperienceProfileSerializer(many=True, read_only=True)

    # Multiple Project entries
    project_profiles = ProjectsProfileSerializer(many=True, read_only=True)

    # Opportunities Interest
    opportunities_interest = serializers.SerializerMethodField()

    # Recommendation Priority
    recommendation_priority = serializers.SerializerMethodField()

    # Parsed Profile Data (from CV)
    parsed_profile_data = serializers.SerializerMethodField()

    # Goals
    user_goals = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            # Basic user info
            'id', 'email', 'first_name', 'last_name', 'country', 'date_joined',

            # Personal info
            'profile_picture', 'phone_number', 'goal',

            # CV info
            'cv_filename', 'cv_uploaded_at', 'has_cv_in_gcs', 'cv_download_url',

            # Career
            'career_profile',

            # Multiple entries
            'education_profiles',
            'experience_profiles',
            'project_profiles',

            # Preferences
            'opportunities_interest',
            'recommendation_priority',

            # Parsed profile
            'parsed_profile_data',

            # Goals
            'user_goals'
        ]

    def get_profile_picture(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.profile_picture:
                return obj.profile.profile_picture.url
        except:
            pass
        return None

    def get_phone_number(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.phone_number
        except:
            pass
        return ""

    def get_goal(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.goal
        except:
            pass
        return ""

    def get_cv_filename(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.cv_filename
        except:
            pass
        return None

    def get_cv_uploaded_at(self, obj):
        try:
            if hasattr(obj, 'profile') and obj.profile.cv_uploaded_at:
                return obj.profile.cv_uploaded_at.isoformat()
        except:
            pass
        return None

    def get_has_cv_in_gcs(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.has_cv_in_gcs()
        except:
            pass
        return False

    def get_cv_download_url(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return obj.profile.get_cv_download_url()
        except:
            pass
        return None

    def get_career_profile(self, obj):
        try:
            career = obj.careerprofile
            return {
                'industry': career.industry,
                'job_title': career.job_title,
                'profile_summary': career.profile_summary
            }
        except:
            return {
                'industry': '',
                'job_title': '',
                'profile_summary': ''
            }

    def get_opportunities_interest(self, obj):
        try:
            interest = obj.opportunitiesinterest
            return {
                'scholarships': interest.scholarships,
                'jobs': interest.jobs,
                'grants': interest.grants,
                'internships': interest.internships
            }
        except:
            return {
                'scholarships': False,
                'jobs': False,
                'grants': False,
                'internships': False
            }

    def get_recommendation_priority(self, obj):
        try:
            priority = obj.recommendationpriority
            return {
                'academic_background': priority.academic_background,
                'work_experience': priority.work_experience,
                'preferred_locations': priority.preferred_locations,
                'others': priority.others,
                'additional_preferences': priority.additional_preferences
            }
        except:
            return {
                'academic_background': False,
                'work_experience': False,
                'preferred_locations': False,
                'others': False,
                'additional_preferences': ''
            }

    def get_parsed_profile_data(self, obj):
        try:
            if hasattr(obj, 'parsed_profile'):
                parsed_profile = obj.parsed_profile
                return {
                    'first_name': parsed_profile.first_name,
                    'last_name': parsed_profile.last_name,
                    'email': parsed_profile.email,
                    'phone': parsed_profile.phone,
                    'address': parsed_profile.address,
                    'linkedin': parsed_profile.linkedin,
                    'portfolio': parsed_profile.portfolio,
                    'summary': parsed_profile.summary,
                    'education': parsed_profile.education,
                    'experience': parsed_profile.experience,
                    'skills': parsed_profile.skills,
                    'certifications': parsed_profile.certifications,
                    'languages': parsed_profile.languages,
                    'projects': parsed_profile.projects,
                    'confidence_score': parsed_profile.confidence_score,
                    'completion_percentage': parsed_profile.completion_percentage,
                    'missing_sections': parsed_profile.missing_sections,
                    'completed_sections': parsed_profile.completed_sections,
                }
        except:
            pass
        return None

    def get_user_goals(self, obj):
        try:
            goals = obj.goals.all().order_by('priority')
            return [
                {
                    'goal': goal.goal,
                    'goal_display': goal.get_goal_display(),
                    'priority': goal.priority
                }
                for goal in goals
            ]
        except:
            return []
