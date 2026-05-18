from django.contrib import admin
from .models import Candidate

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'passport_number', 'job_category', 'application_status', 'age']
    list_filter = ['job_category', 'application_status', 'religion', 'health_clearance']
    search_fields = ['full_name', 'passport_number', 'nin']
    readonly_fields = ['registered_at', 'updated_at']
    
    fieldsets = (
        ('Identity', {
            'fields': ('full_name', 'nin', 'passport_number', 'date_of_birth')
        }),
        ('Demographics', {
            'fields': ('religion', 'gender', 'job_category')
        }),
        ('Health & Status', {
            'fields': ('health_clearance', 'yellow_fever_status', 'application_status')
        }),
        ('Documents', {
            'fields': ('profile_photo', 'passport_copy', 'cv_pdf')
        }),
        ('Metadata', {
            'fields': ('registered_by', 'registered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )  
