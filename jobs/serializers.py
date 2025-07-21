from rest_framework import serializers
from .models import Job, UserJob

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'company',
            'salary',
            'location',
            'job_type',
            'skills',
            'experience_level',
            'posted_at',
        ]

    def validate(self, data):
        errors = {}
        # Required field: title (as per updated requirement)
        if not data.get('title') or str(data.get('title')).strip() == '':
            errors['title'] = ['This field is required and cannot be empty.']
        if errors:
            raise serializers.ValidationError(errors)
        return data


class UserJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    job_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserJob
        fields = [
            'id',
            'job',
            'job_id',
            'applied',
            'applied_date',
            'updated_at',
        ]
        read_only_fields = ['applied_date', 'updated_at']

    def create(self, validated_data):
        job_id = validated_data.pop('job_id')
        validated_data['job_id'] = job_id
        return super().create(validated_data)
