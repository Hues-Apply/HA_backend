from rest_framework import serializers
from opportunities.models import Category, Tag, Opportunity


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']

class OpportunitySerializer(serializers.ModelSerializer):
    # For readable output
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    posted_by = serializers.StringRelatedField(read_only=True)

    # For input (write)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'type', 'organization', 'category', 'category_id', 'location', 'is_remote', 'description', 'eligibility_criteria', 'skills_required', 'tags', 'tag_ids', 'deadline', 'created_at', 'is_verified', 'is_featured', 'application_url', 'application_process', 'posted_by'
        ]
        read_only_fields = ['posted_by', 'created_at']
        
    def create(self, validated_data):
        validated_data['posted_by'] = self.context['request'].user
        return super().create(validated_data)
