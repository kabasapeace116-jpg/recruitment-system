from django import forms
from django.contrib.auth.models import User
from .models import Candidate

class CandidateRegistrationForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = '__all__'
        exclude = ['registered_by', 'registered_at', 'updated_at']
        widgets = {
            'candidate_video': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'video/*'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'nin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Passport number'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'e.g., Driving, Cleaning, First Aid'}),
            'languages_spoken': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., English, Arabic, Swahili'}),
            'medical_conditions': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'home_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'preferred_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., UAE, Saudi Arabia, Qatar'}),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount in USD'}),
            'health_status': forms.Select(attrs={'class': 'form-control'}),
            'visa_document': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class ClientUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirm Password')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@company.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        
        username = cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            self.add_error('username', 'Username already exists')
        
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', 'Email already exists')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            try:
                from django.contrib.auth.models import Group
                group, created = Group.objects.get_or_create(name='Clients')
                user.groups.add(group)
            except:
                pass
        return user