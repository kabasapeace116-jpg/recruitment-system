import django_filters
from django import forms
from .models import Candidate, Religion, JobCategory
from datetime import date, timedelta

class CandidateFilter(django_filters.FilterSet):
    age_min = django_filters.NumberFilter(
        field_name='date_of_birth',
        method='filter_age_min',
        label='Minimum Age'
    )
    age_max = django_filters.NumberFilter(
        field_name='date_of_birth',
        method='filter_age_max',
        label='Maximum Age'
    )
    religion = django_filters.ChoiceFilter(
        choices=Religion.choices,
        empty_label='All Religions'
    )
    job_category = django_filters.ChoiceFilter(
        choices=JobCategory.choices,
        empty_label='All Categories'
    )
    health_clearance = django_filters.BooleanFilter(
        widget=forms.CheckboxInput,
        label='Health Clearance Only'
    )
    yellow_fever_status = django_filters.BooleanFilter(
        widget=forms.CheckboxInput,
        label='Yellow Fever Vaccinated'
    )
    
    class Meta:
        model = Candidate
        fields = ['religion', 'job_category', 'health_clearance', 'yellow_fever_status']
    
    def filter_age_min(self, queryset, name, value):
        if value:
            max_birth_date = date.today() - timedelta(days=value*365.25)
            return queryset.filter(date_of_birth__lte=max_birth_date)
        return queryset
    
    def filter_age_max(self, queryset, name, value):
        if value:
            min_birth_date = date.today() - timedelta(days=value*365.25)
            return queryset.filter(date_of_birth__gte=min_birth_date)
        return queryset  
