from django.contrib import admin
from .models import Opportunity, Category, Tag

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'organization', 'category', 'location', 'deadline', 'is_verified')
    list_filter = ('type', 'is_verified', 'is_featured', 'category')
    search_fields = ('title', 'organization', 'location')
    filter_horizontal = ('tags',)   

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
