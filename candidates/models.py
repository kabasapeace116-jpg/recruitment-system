from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from datetime import date

def profile_photo_path(instance, filename):
    return f'candidates/{instance.passport_number}/photo_{filename}'

def document_path(instance, filename):
    return f'candidates/{instance.passport_number}/docs/{filename}'

class Religion(models.TextChoices):
    MUSLIM = 'MUS', 'Muslim'
    CHRISTIAN = 'CHR', 'Christian'
    OTHER = 'OTH', 'Other'

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'

class JobCategory(models.TextChoices):
    MAID = 'MAID', 'Maid'
    CLEANER = 'CLN', 'Cleaner'
    CAREGIVER = 'CAR', 'Caregiver'
    DRIVER = 'DRV', 'Driver'
    HOME_TEACHER = 'TCH', 'Home Teacher'
    WAITER = 'WTR', 'Waiter'
    WAITRESS = 'WTS', 'Waitress'
    NANNY = 'NAN', 'Nanny'
    SECURITY = 'SEC', 'Security Guard'
    HOUSEKEEPER = 'HOU', 'Housekeeper'
    GARDENER = 'GAR', 'Gardener'
    COOK = 'COK', 'Cook'

class ApplicationStatus(models.TextChoices):
    AVAILABLE = 'AVA', 'Available'
    SELECTED = 'SEL', 'Selected'
    CANCELLED = 'CAN', 'Cancelled'
    VISA_ISSUED = 'VIS', 'Visa Issued'
    RESERVED = 'RES', 'Reserved'
    

class HealthStatus(models.TextChoices):
    FIT = 'FIT', 'Fit'
    UNFIT = 'UNFIT', 'Unfit'
    PENDING = 'PENDING', 'Pending'



class Candidate(models.Model):
    # Personal Information
    full_name = models.CharField(max_length=200, verbose_name="Full Name")
    nin = models.CharField('National ID', max_length=50, unique=True)
    passport_number = models.CharField(max_length=50, unique=True)
    passport_issue_date = models.DateField(verbose_name="Passport Issue Date", null=True, blank=True)
    passport_expiry_date = models.DateField(verbose_name="Passport Expiry Date", null=True, blank=True)
    date_of_birth = models.DateField(verbose_name="Date of Birth")
    place_of_birth = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True)
    alternative_phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    home_address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Demographics
    religion = models.CharField(max_length=3, choices=Religion.choices)
    gender = models.CharField(max_length=1, choices=Gender.choices)
    job_category = models.CharField(max_length=4, choices=JobCategory.choices)
    
    # Professional Information
    years_of_experience = models.IntegerField(default=0)
    skills = models.TextField(help_text="List key skills separated by commas", blank=True)
    languages_spoken = models.CharField(max_length=200, help_text="e.g., English, Arabic, Swahili", blank=True)
    
    
    # Health & Medical
    health_clearance = models.BooleanField(default=False, verbose_name="Health Clearance")
    yellow_fever_status = models.BooleanField(default=False, verbose_name="Yellow Fever Vaccination")
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions to note")
    blood_group = models.CharField(max_length=5, blank=True, choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
    ])
    # NEW 
    health_status = models.CharField(
        max_length=7,
        choices=HealthStatus.choices,
        default=HealthStatus.PENDING,
        verbose_name="Health Status"
    )
    
    # Placement Information
    application_status = models.CharField(
        max_length=3, 
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.AVAILABLE
    )
    preferred_country = models.CharField(max_length=100, blank=True, help_text="Preferred country in Arab world")
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Documents
    profile_photo = models.ImageField(
        upload_to=profile_photo_path,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        null=True, blank=True
    )
    candidate_video = models.FileField(
        upload_to=document_path,
        validators=[FileExtensionValidator(['mp4', 'mov', 'avi', 'webm'])],
        null=True, blank=True,
        help_text="Upload a short video introduction of the candidate (max 50MB)"
    )
    passport_copy = models.FileField(
        upload_to=document_path,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg'])],
        null=True, blank=True
    )
    cv_pdf = models.FileField(
        upload_to=document_path,
        validators=[FileExtensionValidator(['pdf'])],
        null=True, blank=True
    )
    medical_certificate = models.FileField(
        upload_to=document_path,
        null=True, blank=True
    )
    training_certificates = models.FileField(
        upload_to=document_path,
        null=True, blank=True
    )
    visa_document = models.FileField(  
        upload_to=document_path,
        validators=[FileExtensionValidator(['pdf', 'jpg', 'jpeg', 'png'])],
        null=True, blank=True,
        help_text="Upload visa copy or related documents"
    )
    
    
    # Tracking
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    registered_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_candidates'
    )
    notes = models.TextField(blank=True, help_text="Internal notes about the candidate")
    

    
    class Meta:
        indexes = [
            models.Index(fields=['job_category', 'application_status']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['passport_number']),
            models.Index(fields=['passport_expiry_date']),
        ]
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.passport_number}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def passport_valid(self):
        """Check if passport is valid (not expired)"""
        if self.passport_expiry_date:
            return self.passport_expiry_date >= date.today()
        return None
    
    @property
    def status_color(self):
        colors = {
            'AVA': 'success',
            'SEL': 'warning',
            'CAN': 'danger',
            'VIS': 'info',
            'REG': 'secondary',
            'INT': 'primary',
            'MED': 'warning',
            'MCL': 'success',
            'DOC': 'info',
            'VPR': 'warning',
            'PLC': 'success',
            'DEP': 'success',
            'CMP': 'secondary'
        }
        return colors.get(self.application_status, 'secondary')


class ClientSelection(models.Model):
    client = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='selections')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='selected_by_clients')
    selected_at = models.DateTimeField(auto_now_add=True)
    
    # Sponsor Details (filled on confirmation)
    sponsor_name = models.CharField(max_length=200, blank=True, null=True)
    sponsor_address = models.TextField(blank=True, null=True)
    sponsor_contact = models.CharField(max_length=50, blank=True, null=True)
    sponsor_email = models.EmailField(blank=True, null=True)
    booking_notes = models.TextField(blank=True, null=True)
    
    # Status flags
    is_booked = models.BooleanField(default=False)  # True = Booked/Reserved
    is_confirmed = models.BooleanField(default=False)  # True = Confirmed/Selected
    
    class Meta:
        unique_together = ('client', 'candidate')
        ordering = ['-selected_at']
    
    def __str__(self):
        if self.is_confirmed:
            return f"{self.client.username} Confirmed {self.candidate.full_name}"
        elif self.is_booked:
            return f"{self.client.username} Booked {self.candidate.full_name}"
        return f"{self.client.username} Selected {self.candidate.full_name}"