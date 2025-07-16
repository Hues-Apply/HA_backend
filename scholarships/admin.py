from django.contrib import admin
from .models import Scholarship, UserScholarship

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'amount', 'deadline', 'course', 'location', 'scraped_at')
    list_filter = ('source', 'course', 'location', 'scraped_at')
    search_fields = ('title', 'source', 'course', 'location')
    readonly_fields = ('scraped_at',)
    ordering = ('-scraped_at',)

@admin.register(UserScholarship)
class UserScholarshipAdmin(admin.ModelAdmin):
    list_display = ('user', 'scholarship', 'applied', 'applied_date', 'updated_at')
    list_filter = ('applied', 'applied_date', 'updated_at')
    search_fields = ('user__email', 'scholarship__title')
    readonly_fields = ('applied_date', 'updated_at')
    ordering = ('-applied_date',)
