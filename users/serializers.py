from rest_framework import serializers
from .models import (
    CustomUser, UserProfile, CareerProfile, EducationProfile, ExperienceProfile,
    Document, ParsedProfile, UserGoal
)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['name', 'email', 'profile_picture', 'phone_number', 'country', 'goal']


class CareerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerProfile
        fields = ['industry', 'job_title', 'profile_summary']


class EducationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationProfile
        fields = ['degree', 'school', 'start_date', 'end_date', 'extra_curricular']


class ExperienceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExperienceProfile
        fields = ['job_title', 'company_name', 'location']


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
    class Meta:
        model = Document
        fields = [
            'id', 'document_type', 'file', 'original_filename', 
            'processing_status', 'uploaded_at', 'processed_at', 'error_message'
        ]
        read_only_fields = ['id', 'uploaded_at', 'processed_at', 'processing_status', 'error_message', 'original_filename']
    
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
