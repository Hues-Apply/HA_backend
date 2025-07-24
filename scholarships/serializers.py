from rest_framework import serializers
from .models import Scholarship, UserScholarship, ScholarshipProfile 

class ScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scholarship
        fields = [
            'id',
            'title',
            'application_link',
            'source',
            'amount',
            'deadline',
            'course',
            'gpa',
            'location',
            'degree_level', 
            'nationality',
            'scraped_at',
            'overview',
        ]
    
    def validate(self, data):
        errors = {}
        for field in ['title', 'application_link', 'deadline']:
            value = data.get(field)
            if value is None or str(value).strip() == '':
                errors[field] = ['This field is required and cannot be empty.']
        if errors:
            raise serializers.ValidationError(errors)
        return data

class UserScholarshipSerializer(serializers.ModelSerializer):
    scholarship = ScholarshipSerializer(read_only=True)
    scholarship_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserScholarship
        fields = [
            'id',
            'scholarship',
            'scholarship_id',
            'applied',
            'applied_date',
            'updated_at',
        ]
        read_only_fields = ['applied_date', 'updated_at']

    def create(self, validated_data):
        scholarship_id = validated_data.pop('scholarship_id')
        validated_data['scholarship_id'] = scholarship_id
        return super().create(validated_data)
    
    