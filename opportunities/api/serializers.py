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
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    posted_by = serializers.StringRelatedField(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        source='category', queryset=Category.objects.all(), write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Opportunity
        fields = [
            'id', 'title', 'type', 'organization', 'category', 'category_id',
            'location', 'is_remote', 'experience_level',
            'description', 'eligibility_criteria', 'skills_required',
            'tags', 'tag_ids', 'deadline', 'created_at',
            'is_verified', 'is_featured', 'application_url',
            'application_process', 'posted_by'
        ]


class OpportunityRecommendationSerializer(serializers.Serializer):
    id = serializers.IntegerField(source='opportunity.id')
    title = serializers.CharField(source='opportunity.title')
    type = serializers.CharField(source='opportunity.type')
    organization = serializers.CharField(source='opportunity.organization')
    category = serializers.SerializerMethodField()
    location = serializers.CharField(source='opportunity.location')
    is_remote = serializers.BooleanField(source='opportunity.is_remote')
    deadline = serializers.DateField(source='opportunity.deadline')
    experience_level = serializers.CharField(source='opportunity.experience_level')
    score = serializers.IntegerField()
    reasons = serializers.DictField()

    def get_category(self, obj):
        category = obj['opportunity'].category
        return {
            'id': category.id,
            'name': category.name,
            'slug': category.slug
        }
