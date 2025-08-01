from django.contrib import admin
from .models import Opportunity, Category, Tag

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'organization', 'category', 'location', 'deadline', 'is_verified', 'source', 'salary_display')
    list_filter = ('type', 'is_verified', 'is_featured', 'category', 'source', 'is_remote', 'salary_currency')
    search_fields = ('title', 'organization', 'location', 'external_id', 'import_batch_id')
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at', 'search_vector', 'view_count', 'application_count')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'type', 'organization', 'category', 'location', 'is_remote')
        }),
        ('Content', {
            'fields': ('description', 'skills_required', 'tags', 'eligibility_criteria')
        }),
        ('Application Details', {
            'fields': ('deadline', 'application_url', 'application_process')
        }),
        ('Salary Information', {
            'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_period'),
            'classes': ('collapse',)
        }),
        ('Import & Tracking', {
            'fields': ('external_id', 'source', 'import_batch_id'),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('is_verified', 'is_featured', 'is_active')
        }),
        ('Metrics', {
            'fields': ('view_count', 'application_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def salary_display(self, obj):
        """Display formatted salary information"""
        if obj.salary_min and obj.salary_max:
            if obj.salary_min == obj.salary_max:
                return f"{obj.salary_currency} {obj.salary_min:,.0f} per {obj.salary_period}"
            else:
                return f"{obj.salary_currency} {obj.salary_min:,.0f} - {obj.salary_max:,.0f} per {obj.salary_period}"
        elif obj.salary_min:
            return f"{obj.salary_currency} {obj.salary_min:,.0f}+ per {obj.salary_period}"
        return "Not specified"
    salary_display.short_description = "Salary"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
