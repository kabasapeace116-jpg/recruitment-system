import os
import django
import random
import string
from datetime import datetime, timedelta, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment_system.settings')
django.setup()

from candidates.models import Candidate
from django.contrib.auth.models import User
from django.db.models import Count

print("=" * 60)
print("GENERATING 500 SAMPLE CANDIDATES")
print("=" * 60)

# Get admin user
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("✓ Created admin user")

# Job categories
JOB_CATEGORIES = [
    ('MAID', 'Maid'), ('CLN', 'Cleaner'), ('CAR', 'Caregiver'),
    ('DRV', 'Driver'), ('TCH', 'Home Teacher'), ('WTR', 'Waiter'),
    ('WTS', 'Waitress'), ('NAN', 'Nanny'), ('SEC', 'Security'),
    ('HOU', 'Housekeeper'), ('GAR', 'Gardener'), ('COK', 'Cook')
]

# Statuses
STATUSES = ['AVA', 'SEL', 'CAN', 'VIS', 'REG', 'INT']
STATUS_WEIGHTS = [0.4, 0.2, 0.05, 0.1, 0.15, 0.1]

RELIGIONS = ['MUS', 'CHR', 'OTH']
RELIGION_WEIGHTS = [0.4, 0.55, 0.05]

GENDERS = ['M', 'F']
GENDER_WEIGHTS = [0.45, 0.55]

COUNTRIES = ['UAE', 'Saudi Arabia', 'Qatar', 'Kuwait', 'Oman', 'Bahrain']

FIRST_NAMES_MALE = ['John', 'Peter', 'James', 'Robert', 'Michael', 'David', 'Joseph', 'Thomas', 'Charles', 'Paul',
                    'Moses', 'Samuel', 'Daniel', 'Patrick', 'Stephen', 'Andrew', 'Simon', 'Philip', 'Barnabas', 'Timothy']
FIRST_NAMES_FEMALE = ['Sarah', 'Mary', 'Grace', 'Jane', 'Alice', 'Ruth', 'Esther', 'Deborah', 'Rebecca', 'Rachel',
                      'Catherine', 'Elizabeth', 'Margaret', 'Patricia', 'Jennifer', 'Linda', 'Barbara', 'Susan', 'Jessica', 'Karen']
LAST_NAMES = ['Mukasa', 'Nambi', 'Okello', 'Auma', 'Mwangi', 'Ochieng', 'Kwizera', 'Hussein', 'Abdi', 'Ssemwanga',
              'Kato', 'Nakato', 'Bukenya', 'Nabatanzi', 'Ssali', 'Nantongo', 'Lubega', 'Namugga', 'Muwanga', 'Nakintu']

SKILLS_POOL = [
    'Driving', 'Cleaning', 'Childcare', 'Cooking', 'First Aid', 'Customer Service',
    'Teaching', 'Tutoring', 'Security', 'CCTV Monitoring', 'Gardening', 'Housekeeping'
]

LANGUAGES_POOL = ['English', 'Arabic', 'Swahili', 'French', 'Luganda']

def random_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + (end - start) * random.random()

def random_choice_weighted(choices, weights):
    return random.choices(choices, weights=weights, k=1)[0]

def generate_nin():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=10))
    return f"{letters}{numbers}"

def generate_passport():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=7))
    return f"{letters}{numbers}"

# Ask if user wants to delete existing data
response = input("\nDo you want to delete ALL existing candidates? (yes/no): ")
if response.lower() == 'yes':
    deleted = Candidate.objects.all().delete()
    print(f"✓ Deleted {deleted[0]} existing candidates")

print("\n📝 Generating 500 candidates...")
created_count = 0

for i in range(500):
    gender = random_choice_weighted(GENDERS, GENDER_WEIGHTS)
    first_name = random.choice(FIRST_NAMES_MALE if gender == 'M' else FIRST_NAMES_FEMALE)
    last_name = random.choice(LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    
    nin = generate_nin()
    passport_number = generate_passport()
    
    # Ensure uniqueness
    while Candidate.objects.filter(passport_number=passport_number).exists():
        passport_number = generate_passport()
    while Candidate.objects.filter(nin=nin).exists():
        nin = generate_nin()
    
    birth_year = random.randint(1965, 2005)
    dob = random_date(birth_year, birth_year)
    
    passport_issue = random_date(2015, 2023)
    passport_expiry = passport_issue + timedelta(days=random.randint(365*5, 365*10))
    
    status = random_choice_weighted(STATUSES, STATUS_WEIGHTS)
    religion = random_choice_weighted(RELIGIONS, RELIGION_WEIGHTS)
    job_category = random.choice(JOB_CATEGORIES)[0]
    experience = random.randint(0, 20)
    
    num_skills = random.randint(3, 6)
    skills = ', '.join(random.sample(SKILLS_POOL, num_skills))
    
    num_languages = random.randint(1, 3)
    languages = ', '.join(random.sample(LANGUAGES_POOL, num_languages))
    
    health_clearance = random.random() < 0.8
    yellow_fever = random.random() < 0.7
    preferred_country = random.choice(COUNTRIES)
    expected_salary = random.randint(500, 2000)
    
    registered_at = datetime.now() - timedelta(days=random.randint(0, 365))
    
    candidate = Candidate(
        full_name=full_name,
        nin=nin,
        passport_number=passport_number,
        passport_issue_date=passport_issue,
        passport_expiry_date=passport_expiry,
        date_of_birth=dob,
        place_of_birth=random.choice(['Kampala', 'Jinja', 'Gulu', 'Mbale', 'Mbarara']),
        phone_number=f"+256{random.randint(700000000, 799999999)}",
        email=f"{first_name.lower()}.{last_name.lower()}@example.com",
        home_address=f"{random.randint(1, 100)} {random.choice(['Street', 'Road'])}, Kampala",
        emergency_contact_name=random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE),
        emergency_contact_phone=f"+256{random.randint(700000000, 799999999)}",
        religion=religion,
        gender=gender,
        job_category=job_category,
        years_of_experience=experience,
        skills=skills,
        languages_spoken=languages,
        health_clearance=health_clearance,
        yellow_fever_status=yellow_fever,
        medical_conditions=random.choice(['None', 'None', 'None', 'Asthma']),
        blood_group=random.choice(['A+', 'B+', 'O+', '']),
        application_status=status,
        preferred_country=preferred_country,
        expected_salary=expected_salary,
        registered_by=admin_user,
        registered_at=registered_at,
        notes=f"Auto-generated candidate"
    )
    candidate.save()
    created_count += 1
    
    if (i + 1) % 50 == 0:
        print(f"   Generated {i + 1}/500 candidates...")

print(f"\n✅ Successfully created {created_count} new candidates!")

# Display summary
print("\n" + "=" * 60)
print("📊 CANDIDATES SUMMARY")
print("=" * 60)

print("\n📋 By Status:")
status_counts = Candidate.objects.values('application_status').annotate(count=Count('id'))
status_names = {'AVA': 'Available', 'SEL': 'Selected', 'CAN': 'Cancelled', 'VIS': 'Visa Issued', 'REG': 'Registered', 'INT': 'Interviewed'}
for item in status_counts:
    name = status_names.get(item['application_status'], item['application_status'])
    print(f"   {name}: {item['count']}")

print("\n💼 By Job Category (Top 8):")
job_counts = Candidate.objects.values('job_category').annotate(count=Count('id'))
job_names = dict(JOB_CATEGORIES)
for item in job_counts[:8]:
    name = job_names.get(item['job_category'], item['job_category'])
    print(f"   {name}: {item['count']}")

print("\n👥 By Gender:")
print(f"   Male: {Candidate.objects.filter(gender='M').count()}")
print(f"   Female: {Candidate.objects.filter(gender='F').count()}")

print("\n" + "=" * 60)
print("🎉 DONE! Run your server to see the data:")
print("   python manage.py runserver")
print("=" * 60)