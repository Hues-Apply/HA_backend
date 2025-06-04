from rest_framework import serializers
from .models import CustomUser, UserProfile, CareerProfile, EducationProfile, ExperienceProfile

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
