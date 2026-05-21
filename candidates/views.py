from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.models import User, Group
from datetime import datetime, timedelta, date
import json
from .models import Candidate, JobCategory
from .models import Candidate, JobCategory, ClientSelection
from .forms import CandidateRegistrationForm, ClientUserCreationForm
from .models import Candidate, JobCategory, Religion, ApplicationStatus, HealthStatus, ClientSelection

from django.contrib.auth import get_user_model
User = get_user_model()

def ensure_admin_user_exists():
    """Create default admin user if no users exist"""
    if not User.objects.exists():
        # Create admin user
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@mahikeng.com',
            password='admin123'
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print("✓ Default admin created - Username: admin, Password: admin123")
        
        # Also create a demo client user
        client = User.objects.create_user(
            username='demo_client',
            email='client@demo.com',
            password='client123'
        )
        client.is_staff = False
        client.is_superuser = False
        client.save()
        print("✓ Demo client created - Username: demo_client, Password: client123")

def home_redirect(request):
    """Redirect to admin dashboard if logged in, otherwise to login"""
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('admin_dashboard'))
    else:
        return HttpResponseRedirect('/admin/login/?next=/admin-dashboard/')

def is_admin_user(user):
    return user.is_staff or user.is_superuser

def is_client_user(user):
    return user.is_authenticated and not user.is_staff


from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    # Get all candidates
    all_candidates = Candidate.objects.select_related('registered_by').all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    page_number = request.GET.get('page', 1)
    
    # Apply search filter
    if search_query:
        all_candidates = all_candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_number__icontains=search_query) |
            Q(nin__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        all_candidates = all_candidates.filter(application_status=status_filter)
    
    # Get IDs of candidates that have been selected by clients
    selected_candidate_ids = ClientSelection.objects.values_list('candidate_id', flat=True).distinct()
    
    # Annotate each candidate with selection status
    for candidate in all_candidates:
        candidate.is_selected_by_client = candidate.id in selected_candidate_ids
    
    # Stats Cards
    total_candidates = Candidate.objects.count()
    registered_today = Candidate.objects.filter(registered_at__date=datetime.now().date()).count()
    available_count = Candidate.objects.filter(application_status='AVA').count()
    
    # COUNT SELECTED BY CLIENTS (unique candidates)
    selected_by_clients_count = len(selected_candidate_ids)
    
    # For the table - with pagination
    paginator = Paginator(all_candidates, 999999)  # Show all
    page_obj = paginator.get_page(page_number)
    
    # Recent candidates
    recent_candidates = Candidate.objects.all()[:10]
    for candidate in recent_candidates:
        candidate.is_selected_by_client = candidate.id in selected_candidate_ids
    
    # Job category distribution for chart
    job_distribution = Candidate.objects.values('job_category').annotate(count=Count('id'))
    job_labels = []
    job_data = []
    job_map = dict(JobCategory.choices)
    
    for item in job_distribution:
        job_labels.append(job_map.get(item['job_category'], item['job_category']))
        job_data.append(item['count'])
    
    if not job_labels:
        job_labels = ['Maid', 'Cleaner', 'Caregiver', 'Driver', 'Home Teacher', 'Waiter', 'Waitress']
        job_data = [0, 0, 0, 0, 0, 0, 0]
    
    # Monthly SELECTED BY CLIENTS (candidates that were selected by clients)
    months = []
    selected_data = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_name = month_date.strftime('%B')
        months.append(month_name)
        
        if month_date.month == 12:
            month_start = date(month_date.year, month_date.month, 1)
            month_end = date(month_date.year + 1, 1, 1)
        else:
            month_start = date(month_date.year, month_date.month, 1)
            month_end = date(month_date.year, month_date.month + 1, 1)
        
        # Count unique candidates selected by clients in this month
        month_selected = ClientSelection.objects.filter(
            selected_at__date__gte=month_start,
            selected_at__date__lt=month_end
        ).values('candidate').distinct().count()
        selected_data.append(month_selected)
    
    context = {
        'total_candidates': total_candidates,
        'registered_today': registered_today,
        'available_count': available_count,
        'selected_by_clients_count': selected_by_clients_count,
        'page_obj': page_obj,
        'recent_candidates': recent_candidates,
        'job_labels': job_labels,
        'job_data': job_data,
        'months': months,
        'selected_data': selected_data,
        'search_query': search_query,
        'status_filter': status_filter,
        'selected_candidate_ids': list(selected_candidate_ids),
    }
    
    return render(request, 'recruitment/admin_dashboard.html', context)
    # Get all candidates
    all_candidates = Candidate.objects.select_related('registered_by').all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    page_number = request.GET.get('page', 1)
    
    # Apply search filter
    if search_query:
        all_candidates = all_candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_number__icontains=search_query) |
            Q(nin__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        all_candidates = all_candidates.filter(application_status=status_filter)
    
    # Stats Cards (using ALL candidates for true totals)
    total_candidates = Candidate.objects.count()
    registered_today = Candidate.objects.filter(registered_at__date=datetime.now().date()).count()
    available_count = Candidate.objects.filter(application_status='AVA').count()
    
    # COUNT SELECTED BY CLIENTS (not just status='SEL')
    selected_by_clients_count = ClientSelection.objects.values('candidate').distinct().count()
    
    # For the table - with pagination
    paginator = Paginator(all_candidates, 10)
    page_obj = paginator.get_page(page_number)
    
    # Recent candidates
    recent_candidates = Candidate.objects.all()[:10]
    
    # Job category distribution for chart
    job_distribution = Candidate.objects.values('job_category').annotate(count=Count('id'))
    job_labels = []
    job_data = []
    job_map = dict(JobCategory.choices)
    
    for item in job_distribution:
        job_labels.append(job_map.get(item['job_category'], item['job_category']))
        job_data.append(item['count'])
    
    if not job_labels:
        job_labels = ['Maid', 'Cleaner', 'Caregiver', 'Driver', 'Home Teacher', 'Waiter', 'Waitress']
        job_data = [0, 0, 0, 0, 0, 0, 0]
    
    # Monthly SELECTED BY CLIENTS (candidates that were selected by clients, not just status)
    months = []
    selected_data = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        month_name = month_date.strftime('%B')
        months.append(month_name)
        
        # Get first and last day of the month
        if month_date.month == 12:
            month_start = date(month_date.year, month_date.month, 1)
            month_end = date(month_date.year + 1, 1, 1)
        else:
            month_start = date(month_date.year, month_date.month, 1)
            month_end = date(month_date.year, month_date.month + 1, 1)
        
        # Count candidates that were SELECTED BY CLIENTS in this month
        month_selected = ClientSelection.objects.filter(
            selected_at__date__gte=month_start,
            selected_at__date__lt=month_end
        ).values('candidate').distinct().count()
        selected_data.append(month_selected)
    
    context = {
        'total_candidates': total_candidates,
        'registered_today': registered_today,
        'available_count': available_count,
        'selected_by_clients_count': selected_by_clients_count,
        'page_obj': page_obj,
        'recent_candidates': recent_candidates,
        'job_labels': job_labels,
        'job_data': job_data,
        'months': months,
        'selected_data': selected_data,
        'search_query': search_query,
        'status_filter': status_filter,
        'current_page': int(page_number),
        'total_pages': paginator.num_pages,
    }
    
    return render(request, 'recruitment/admin_dashboard.html', context)
    # Get all candidates (no filtering)
    all_candidates = Candidate.objects.select_related('registered_by').all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Apply search filter
    if search_query:
        all_candidates = all_candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_number__icontains=search_query) |
            Q(nin__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter and status_filter != 'all':
        all_candidates = all_candidates.filter(application_status=status_filter)
    
    # Stats Cards
    total_candidates = Candidate.objects.count()
    registered_today = Candidate.objects.filter(registered_at__date=datetime.now().date()).count()
    available_count = Candidate.objects.filter(application_status='AVA').count()
    selected_count = Candidate.objects.filter(application_status='SEL').count()
    
    # For the table - with pagination (10 per page)
    paginator = Paginator(all_candidates, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Recent candidates (last 10 for the second table)
    recent_candidates = Candidate.objects.all()[:10]
    
    # Job category distribution for chart
    job_distribution = Candidate.objects.values('job_category').annotate(count=Count('id'))
    job_labels = []
    job_data = []
    job_map = dict(JobCategory.choices)
    
    for item in job_distribution:
        job_labels.append(job_map.get(item['job_category'], item['job_category']))
        job_data.append(item['count'])
    
    if not job_labels:
        job_labels = ['Maid', 'Cleaner', 'Caregiver', 'Driver', 'Home Teacher', 'Waiter', 'Waitress']
        job_data = [0, 0, 0, 0, 0, 0, 0]
    
    # Monthly SELECTED candidates (not placements)
    months = []
    selected_data = []
    today = datetime.now().date()
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30*i)
        months.append(month_date.strftime('%B'))
        
        month_start = date(month_date.year, month_date.month, 1)
        if month_date.month == 12:
            month_end = date(month_date.year + 1, 1, 1)
        else:
            month_end = date(month_date.year, month_date.month + 1, 1)
        
        # Count candidates marked as SELECTED in this month
        month_selected = Candidate.objects.filter(
            application_status='SEL',
            updated_at__date__gte=month_start,
            updated_at__date__lt=month_end
        ).count()
        selected_data.append(month_selected)
    
    context = {
        'total_candidates': total_candidates,
        'registered_today': registered_today,
        'available_count': available_count,
        'selected_count': selected_count,
        'page_obj': page_obj,
        'recent_candidates': recent_candidates,
        'job_labels': job_labels,
        'job_data': job_data,
        'months': months,
        'selected_data': selected_data,  # Changed from placements_data
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'recruitment/admin_dashboard.html', context)


@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def candidate_create(request):
    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.registered_by = request.user
            candidate.save()
            messages.success(request, f'Candidate "{candidate.full_name}" registered successfully!')
            return redirect('candidate_detail', pk=candidate.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return render(request, 'recruitment/candidate_form.html', {'form': form})
    else:
        form = CandidateRegistrationForm()
    
    return render(request, 'recruitment/candidate_form.html', {'form': form})
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def candidate_detail(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, 'recruitment/candidate_detail.html', {'candidate': candidate})

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def candidate_update(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    
    if request.method == 'POST':
        form = CandidateRegistrationForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, f'Candidate "{candidate.full_name}" updated successfully!')
            # IMPORTANT: Redirect to detail page, NOT back to form
            return redirect('candidate_detail', pk=candidate.pk)
        else:
            # Form has errors - show messages and stay on form
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            # Stay on the edit page with errors
            return render(request, 'recruitment/candidate_form.html', {'form': form, 'candidate': candidate})
    else:
        form = CandidateRegistrationForm(instance=candidate)
    
    return render(request, 'recruitment/candidate_form.html', {'form': form, 'candidate': candidate})
@login_required(login_url='/client-login/')
def client_portal(request):
    """Show ONLY available candidates to clients"""
    
    # Only show candidates with status 'AVA' (Available)
    candidates = Candidate.objects.filter(application_status='AVA').order_by('-registered_at')
    
    # Apply filters from GET parameters
    age_min = request.GET.get('age_min')
    age_max = request.GET.get('age_max')
    religion = request.GET.get('religion')
    job_category = request.GET.get('job_category')
    health_clearance = request.GET.get('health_clearance')
    yellow_fever = request.GET.get('yellow_fever')
    exp_min = request.GET.get('exp_min')
    exp_max = request.GET.get('exp_max')
    
    # Age filtering
    if age_min:
        try:
            max_birth_date = date.today() - timedelta(days=int(age_min)*365.25)
            candidates = candidates.filter(date_of_birth__lte=max_birth_date)
        except (ValueError, TypeError):
            pass
    
    if age_max:
        try:
            min_birth_date = date.today() - timedelta(days=int(age_max)*365.25)
            candidates = candidates.filter(date_of_birth__gte=min_birth_date)
        except (ValueError, TypeError):
            pass
    
    # Other filters
    if religion:
        candidates = candidates.filter(religion=religion)
    
    if job_category:
        candidates = candidates.filter(job_category=job_category)
    
    if health_clearance:
        candidates = candidates.filter(health_clearance=(health_clearance == 'true'))
    
    if yellow_fever:
        candidates = candidates.filter(yellow_fever_status=(yellow_fever == 'true'))
    
    if exp_min:
        try:
            candidates = candidates.filter(years_of_experience__gte=int(exp_min))
        except (ValueError, TypeError):
            pass
    
    if exp_max:
        try:
            candidates = candidates.filter(years_of_experience__lte=int(exp_max))
        except (ValueError, TypeError):
            pass
    
    # Get IDs of candidates SELECTED by this client (is_booked=False)
    selected_candidates = ClientSelection.objects.filter(
        client=request.user,
        is_booked=False
    ).values_list('candidate_id', flat=True)
    
    # Get IDs of candidates BOOKED by this client (is_booked=True)
    booked_candidates = ClientSelection.objects.filter(
        client=request.user,
        is_booked=True
    ).values_list('candidate_id', flat=True)
    
    # Pagination
    paginator = Paginator(candidates, 999999)  # Show all
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'recruitment/client_portal.html', {
        'candidates': page_obj,
        'page_obj': page_obj,
        'total_count': candidates.count(),
        'selected_candidates': list(selected_candidates),
        'booked_candidates': list(booked_candidates),
    })
@login_required(login_url='/client-login/')
def client_candidate_detail(request, pk):
    candidate = get_object_or_404(
        Candidate, 
        pk=pk, 
        application_status__in=['REG', 'INT', 'MCL']
    )
    return render(request, 'recruitment/client_candidate_detail.html', {'candidate': candidate})

@login_required(login_url='/client-login/')
def client_candidate_detail(request, pk):
    """Show full candidate details - with better error handling"""
    try:
        candidate = get_object_or_404(Candidate, pk=pk)
        return render(request, 'recruitment/client_candidate_detail.html', {'candidate': candidate})
    except Candidate.DoesNotExist:
        messages.error(request, f'Candidate with ID {pk} does not exist.')
        return redirect('client_portal')


    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('client_login')
    else:
        form = ClientRegistrationForm()
    return render(request, 'recruitment/client_register.html', {'form': form})
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def api_candidates(request):
    """Simple API to check candidates"""
    candidates = Candidate.objects.all().values('id', 'full_name', 'application_status', 'has_photo')
    return JsonResponse(list(candidates), safe=False)
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
from .forms import ClientUserCreationForm

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def manage_clients(request):
    """View to manage client users"""
    clients = User.objects.filter(is_staff=False, is_superuser=False).exclude(username=request.user.username)
    
    # Get client group
    client_group, created = Group.objects.get_or_create(name='Clients')
    
    # Stats
    total_clients = clients.count()
    active_clients = clients.filter(is_active=True).count()
    new_this_month = clients.filter(date_joined__month=datetime.now().month).count()
    
    context = {
        'clients': clients,
        'total_clients': total_clients,
        'active_clients': active_clients,
        'new_this_month': new_this_month,
    }
    return render(request, 'recruitment/manage_clients.html', context)


@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def create_client_user(request):
    """Create a new client user"""
    if request.method == 'POST':
        form = ClientUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            # Add to clients group
            from django.contrib.auth.models import Group
            client_group, created = Group.objects.get_or_create(name='Clients')
            user.groups.add(client_group)
            
            # Store phone number in user profile if using extended model
            phone_number = form.cleaned_data.get('phone_number', '')
            if phone_number:
                # If you have UserProfile model, save it there
                # Otherwise, you can store it in a separate model
                pass
            
            messages.success(request, f'Client user "{user.username}" created successfully!')
            return redirect('manage_clients')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientUserCreationForm()
    
    return render(request, 'recruitment/create_client.html', {'form': form})
    """Create a new client user"""
    if request.method == 'POST':
        form = ClientUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            # Add to clients group
            client_group, created = Group.objects.get_or_create(name='Clients')
            user.groups.add(client_group)
            
            # Create user profile if using extended model
            if hasattr(user, 'profile'):
                user.profile.phone_number = form.cleaned_data.get('phone_number', '')
                user.profile.created_by = request.user
                user.profile.save()
            
            messages.success(request, f'Client user "{user.username}" created successfully!')
            return redirect('manage_clients')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientUserCreationForm()
    
    return render(request, 'recruitment/create_client.html', {'form': form})

   

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def toggle_client_status(request, user_id):
    """Enable or disable a client user"""
    client = get_object_or_404(User, id=user_id, is_staff=False)
    client.is_active = not client.is_active
    client.save()
    status = "activated" if client.is_active else "deactivated"
    messages.success(request, f'Client "{client.username}" has been {status}.')
    return redirect('manage_clients')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def reset_client_password(request, user_id):
    """Reset client password"""
    client = get_object_or_404(User, id=user_id, is_staff=False)
    new_password = User.objects.make_random_password(length=10)
    client.set_password(new_password)
    client.save()
    
    messages.success(request, f'Password for "{client.username}" has been reset to: {new_password}')
    return redirect('manage_clients')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def delete_client(request, user_id):
    """Delete a client user"""
    client = get_object_or_404(User, id=user_id, is_staff=False)
    username = client.username
    client.delete()
    messages.success(request, f'Client "{username}" has been deleted.')
    return redirect('manage_clients')

from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.contrib import messages

def admin_login_view(request):
    """Custom admin login view"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('client_portal')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'recruitment/admin_login.html')

def client_login_view(request):
    """Custom client login view"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('client_portal')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'recruitment/client_login.html')

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

def admin_logout_view(request):
    """Custom admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')

def client_logout_view(request):
    """Custom client logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('client_login')

from django.http import JsonResponse
import json



@login_required(login_url='/admin-login/')
@user_passes_test(is_admin_user)
def mass_delete_candidates(request):
    """Delete multiple candidates at once"""
    if request.method == 'POST':
        candidate_ids = json.loads(request.POST.get('candidate_ids', '[]'))
        if candidate_ids:
            candidates = Candidate.objects.filter(id__in=candidate_ids)
            count = candidates.count()
            candidates.delete()
            messages.success(request, f'Successfully deleted {count} candidate(s).')
        else:
            messages.error(request, 'No candidates selected for deletion.')
    return redirect('admin_dashboard')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
@csrf_exempt
def place_candidate(request):
    """Place a candidate and update status to SELECTED"""
    if request.method == 'POST':
        try:
            candidate_id = request.POST.get('candidate_id')
            employer_name = request.POST.get('employer_name')
            country = request.POST.get('country')
            salary = request.POST.get('salary')
            contract_end = request.POST.get('contract_end')
            notes = request.POST.get('notes', '')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Update candidate status to SELECTED
            candidate.application_status = 'SEL'  # Selected status
            candidate.notes = f"{candidate.notes}\n\n--- PLACEMENT DETAILS ---\nEmployer: {employer_name}\nCountry: {country}\nSalary: ${salary}\nContract End: {contract_end}\nPlaced by: {request.user.username}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{notes}"
            candidate.save()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'employer': employer_name,
                    'salary': salary,
                    'country': country,
                    'status': 'SELECTED'
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
    """Place a candidate and update status to SELECTED"""
    if request.method == 'POST':
        try:
            candidate_id = request.POST.get('candidate_id')
            employer_name = request.POST.get('employer_name')
            country = request.POST.get('country')
            salary = request.POST.get('salary')
            contract_end = request.POST.get('contract_end')
            notes = request.POST.get('notes', '')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Update candidate status to SELECTED
            candidate.application_status = 'SEL'  # Selected status
            candidate.notes = f"{candidate.notes}\n\n--- PLACEMENT DETAILS ---\nEmployer: {employer_name}\nCountry: {country}\nSalary: ${salary}\nContract End: {contract_end}\nPlaced by: {request.user.username}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{notes}"
            candidate.save()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'employer': employer_name,
                    'salary': salary,
                    'country': country,
                    'status': 'SELECTED'
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def mass_delete_candidates(request):
    """Delete multiple candidates at once"""
    if request.method == 'POST':
        try:
            data = json.loads(request.POST.get('candidate_ids', '[]'))
            ids = data if isinstance(data, list) else json.loads(data)
            candidates = Candidate.objects.filter(id__in=ids)
            count = candidates.count()
            candidates.delete()
            messages.success(request, f'Successfully deleted {count} candidate(s).')
        except Exception as e:
            messages.error(request, f'Error deleting candidates: {str(e)}')
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')
    """Place a candidate (mark as placed/unavailable)"""
    if request.method == 'POST':
        try:
            candidate_id = request.POST.get('candidate_id')
            employer_name = request.POST.get('employer_name')
            country = request.POST.get('country')
            salary = request.POST.get('salary')
            contract_end = request.POST.get('contract_end')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Update candidate with placement information
            candidate.is_placed = True
            candidate.application_status = 'PLC'  # Placed - Unavailable
            candidate.placed_date = datetime.now()
            candidate.placed_with = employer_name
            candidate.placement_country = country
            candidate.monthly_salary_placed = salary
            candidate.placement_contract_end = contract_end
            
            candidate.save()
            
            return JsonResponse({
                'success': True,
                'data': {
                    'employer': employer_name,
                    'salary': salary,
                    'country': country
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required(login_url='/admin-login/')
@user_passes_test(is_admin_user)
def unplace_candidate(request, pk):
    """Mark a candidate as available again (undo placement)"""
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate.is_placed = False
    candidate.application_status = 'REG'  # Back to registered
    candidate.placed_date = None
    candidate.placed_with = ''
    candidate.placement_country = ''
    candidate.monthly_salary_placed = None
    candidate.placement_contract_end = None
    candidate.save()
    messages.success(request, f'{candidate.full_name} has been marked as available again.')
    return redirect('admin_dashboard')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def delete_candidate(request, pk):
    """Delete a single candidate"""
    candidate = get_object_or_404(Candidate, pk=pk)
    candidate_name = candidate.full_name
    candidate.delete()
    messages.success(request, f'Candidate "{candidate_name}" has been deleted successfully.')
    return redirect('admin_dashboard')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def mass_delete_candidates(request):
    """Delete multiple candidates at once"""
    if request.method == 'POST':
        try:
            import json
            data = request.POST.get('candidate_ids', '[]')
            ids = json.loads(data) if isinstance(data, str) else data
            candidates = Candidate.objects.filter(id__in=ids)
            count = candidates.count()
            candidates.delete()
            messages.success(request, f'Successfully deleted {count} candidate(s).')
        except Exception as e:
            messages.error(request, f'Error deleting candidates: {str(e)}')
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def toggle_client_status(request, user_id):
    """Enable or disable a client user"""
    from django.contrib.auth.models import User
    client = get_object_or_404(User, id=user_id, is_staff=False)
    client.is_active = not client.is_active
    client.save()
    status = "activated" if client.is_active else "deactivated"
    messages.success(request, f'Client "{client.username}" has been {status}.')
    return redirect('manage_clients')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def reset_client_password(request, user_id):
    """Reset client password"""
    from django.contrib.auth.models import User
    from django.contrib.auth.hashers import make_password
    import random
    import string
    
    client = get_object_or_404(User, id=user_id, is_staff=False)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    client.password = make_password(new_password)
    client.save()
    
    messages.success(request, f'Password for "{client.username}" has been reset to: {new_password}')
    return redirect('manage_clients')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def delete_client(request, user_id):
    """Delete a client user"""
    from django.contrib.auth.models import User
    client = get_object_or_404(User, id=user_id, is_staff=False)
    username = client.username
    client.delete()
    messages.success(request, f'Client "{username}" has been deleted.')
    return redirect('manage_clients')

from django.contrib.auth.models import User, Group
from .forms import ClientUserCreationForm

def client_register(request):
    """Client registration view"""
    if request.method == 'POST':
        form = ClientUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            # Add to clients group
            client_group, created = Group.objects.get_or_create(name='Clients')
            user.groups.add(client_group)
            
            messages.success(request, 'Registration successful! Please login.')
            return redirect('client_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientUserCreationForm()
    
    return render(request, 'recruitment/client_register.html', {'form': form})

from django.contrib.auth import authenticate, login, get_user_model
from django.shortcuts import redirect, render
from django.contrib import messages

User = get_user_model()

def ensure_admin_user_exists():
    """Create default admin user if no users exist"""
    if not User.objects.exists():
        # Create admin user
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@mahikeng.com',
            password='admin123'
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        
        # Create demo client user
        client = User.objects.create_user(
            username='demo_client',
            email='client@demo.com',
            password='client123'
        )
        client.is_staff = False
        client.is_superuser = False
        client.save()

def admin_login_view(request):
    """Custom admin login view"""
    ensure_admin_user_exists()  # Ensure users exist
    
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('client_portal')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'recruitment/admin_login.html')

def client_login_view(request):
    """Custom client login view"""
    ensure_admin_user_exists()  # Ensure users exist
    
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('client_portal')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'recruitment/client_login.html')
    """Custom client login view"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('client_portal')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'recruitment/client_login.html')

def admin_logout_view(request):
    """Custom admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')

def client_logout_view(request):
    """Custom client logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('client_login')

def home_redirect(request):
    """Redirect to appropriate dashboard based on user type"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        else:
            return redirect('client_portal')
    return redirect('admin_login')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


from django.views.decorators.csrf import csrf_exempt
import json

@login_required(login_url='/client-login/')
@csrf_exempt
def toggle_select_candidate(request):
    """Client can select or unselect a candidate"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            action = data.get('action')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            if action == 'select':
                # Check if candidate is already booked by this client
                existing_booking = ClientSelection.objects.filter(
                    client=request.user,
                    candidate=candidate,
                    is_booked=True
                ).first()
                
                if existing_booking:
                    return JsonResponse({'success': False, 'message': 'Candidate is already booked. Cannot select.'})
                
                # Create selection (not booked)
                selection, created = ClientSelection.objects.get_or_create(
                    client=request.user,
                    candidate=candidate,
                    defaults={'is_booked': False}
                )
                
                if created:
                    # Update candidate status to SELECTED only if not already RESERVED
                    if candidate.application_status != 'RES':
                        candidate.application_status = 'SEL'
                        candidate.save()
                    return JsonResponse({'success': True, 'message': 'Candidate selected successfully'})
                else:
                    return JsonResponse({'success': False, 'message': 'Already selected'})
            
            elif action == 'unselect':
                # Delete only selections that are NOT booked
                ClientSelection.objects.filter(
                    client=request.user,
                    candidate=candidate,
                    is_booked=False
                ).delete()
                
                # Check if candidate has any other selections or bookings
                if not ClientSelection.objects.filter(candidate=candidate).exists():
                    candidate.application_status = 'AVA'
                    candidate.save()
                return JsonResponse({'success': True, 'message': 'Candidate removed from selection'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
    """Client can select or unselect a candidate"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            action = data.get('action')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            if action == 'select':
                # Create selection
                selection, created = ClientSelection.objects.get_or_create(
                    client=request.user,
                    candidate=candidate,
                    defaults={'is_booked': False}
                )
                if created:
                    # Update candidate status to SELECTED
                    candidate.application_status = 'SEL'
                    candidate.save()
                    return JsonResponse({'success': True, 'message': 'Candidate selected successfully'})
                else:
                    return JsonResponse({'success': False, 'message': 'Already selected'})
            
            elif action == 'unselect':
                # Remove selection
                ClientSelection.objects.filter(client=request.user, candidate=candidate).delete()
                # Check if other clients have selected this candidate
                if not ClientSelection.objects.filter(candidate=candidate).exists():
                    candidate.application_status = 'AVA'
                    candidate.save()
                return JsonResponse({'success': True, 'message': 'Candidate removed from selection'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required(login_url='/client-login/')
@csrf_exempt
def book_candidate(request):
    """Client books a candidate - changes status to RESERVED"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Create or update selection as booked (without sponsor details yet)
            selection, created = ClientSelection.objects.update_or_create(
                client=request.user,
                candidate=candidate,
                defaults={
                    'is_booked': True,
                    'is_confirmed': False,  # Not confirmed yet
                    'selected_at': datetime.now()
                }
            )
            
            # Update candidate status to RESERVED
            candidate.application_status = 'RES'
            candidate.save()
            
            return JsonResponse({'success': True, 'message': 'Candidate booked successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required(login_url='/client-login/')
def client_reservations(request):
    """Show all booked/reserved candidates by the client"""
    # Only get selections where is_booked = True
    bookings = ClientSelection.objects.filter(
        client=request.user,
        is_booked=True  # This ensures only booked candidates appear here
    ).select_related('candidate')
    
    return render(request, 'recruitment/client_reservations.html', {
        'bookings': bookings,
        'total_count': bookings.count()
    })
    """Show all booked/reserved candidates by the client"""
    bookings = ClientSelection.objects.filter(
        client=request.user,
        is_booked=True
    ).select_related('candidate')
    
    return render(request, 'recruitment/client_reservations.html', {
        'bookings': bookings,
        'total_count': bookings.count()
    })


@login_required(login_url='/client-login/')
def client_selections(request):
    """Show all candidates selected by the client (NOT booked)"""
    # Only get selections where is_booked = False
    selections = ClientSelection.objects.filter(
        client=request.user,
        is_booked=False  # This ensures booked candidates don't appear here
    ).select_related('candidate')
    
    return render(request, 'recruitment/client_selections.html', {
        'selections': selections,
        'total_count': selections.count()
    })

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def admin_selections(request):
    """View all client selections (ONLY selections, NOT bookings)"""
    # Only get selections where is_booked = False
    selections = ClientSelection.objects.filter(is_booked=False).select_related('client', 'candidate')
    
    # Get bookings separately for stats
    bookings = ClientSelection.objects.filter(is_booked=True).select_related('client', 'candidate')
    
    # Stats
    total_selections = selections.count()
    total_bookings = bookings.count()
    unique_candidates = selections.values('candidate').distinct().count()
    unique_clients = selections.values('client').distinct().count()
    
    context = {
        'selections': selections,
        'bookings': bookings,
        'total_selections': total_selections,
        'total_bookings': total_bookings,
        'unique_candidates': unique_candidates,
        'unique_clients': unique_clients,
    }
    return render(request, 'recruitment/admin_selections.html', context)

from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password
import random
import string

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def manage_admin_users(request):
    """View to manage admin users (staff/superusers)"""
    admin_users = User.objects.filter(is_staff=True).order_by('-date_joined')
    
    # Get stats
    total_admins = admin_users.count()
    super_admins = admin_users.filter(is_superuser=True).count()
    staff_users = admin_users.filter(is_superuser=False, is_staff=True).count()
    
    context = {
        'admin_users': admin_users,
        'total_admins': total_admins,
        'super_admins': super_admins,
        'staff_users': staff_users,
    }
    return render(request, 'recruitment/manage_admin_users.html', context)

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def create_admin_user(request):
    """Create a new admin/staff user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_type = request.POST.get('user_type')  # 'superadmin' or 'staff'
        
        # Validation
        errors = []
        if not username:
            errors.append('Username is required')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists')
        
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already exists')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        if errors:
            messages.error(request, ' '.join(errors))
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=(user_type == 'superadmin')
            )
            messages.success(request, f'Admin user "{username}" created successfully!')
            return redirect('manage_admin_users')
    
    return render(request, 'recruitment/create_admin_user.html')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def toggle_admin_status(request, user_id):
    """Enable or disable an admin user"""
    admin_user = get_object_or_404(User, id=user_id, is_staff=True)
    # Prevent disabling yourself
    if admin_user.id == request.user.id:
        messages.error(request, 'You cannot disable your own account!')
    else:
        admin_user.is_active = not admin_user.is_active
        admin_user.save()
        status = "activated" if admin_user.is_active else "deactivated"
        messages.success(request, f'Admin "{admin_user.username}" has been {status}.')
    return redirect('manage_admin_users')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def reset_admin_password(request, user_id):
    """Reset admin user password"""
    admin_user = get_object_or_404(User, id=user_id, is_staff=True)
    
    # Generate random password
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    admin_user.set_password(new_password)
    admin_user.save()
    
    messages.success(request, f'Password for "{admin_user.username}" has been reset to: {new_password}')
    return redirect('manage_admin_users')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def delete_admin_user(request, user_id):
    """Delete an admin user"""
    admin_user = get_object_or_404(User, id=user_id, is_staff=True)
    
    # Prevent deleting yourself
    if admin_user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
    else:
        username = admin_user.username
        admin_user.delete()
        messages.success(request, f'Admin user "{username}" has been deleted.')
    return redirect('manage_admin_users')
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.db.utils import OperationalError

@csrf_exempt
def health_check(request):
    """Simple health check endpoint for cron jobs"""
    # Check database connection
    db_connected = False
    try:
        connections['default'].cursor()
        db_connected = True
    except OperationalError:
        pass
    
    return JsonResponse({
        'status': 'ok',
        'database': 'connected' if db_connected else 'disconnected'
    })

from django.db.models import Q

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def candidates_table(request):
    # Get all candidates
    all_candidates = Candidate.objects.select_related('registered_by').all()
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    job_filter = request.GET.get('job', '')
    exp_filter = request.GET.get('exp', '')
    age_filter = request.GET.get('age', '')
    religion_filter = request.GET.get('religion', '')
    status_filter = request.GET.get('status', '')
    health_filter = request.GET.get('health', '')
    
    # Apply search filter
    if search_query:
        all_candidates = all_candidates.filter(
            Q(full_name__icontains=search_query) |
            Q(passport_number__icontains=search_query) |
            Q(nin__icontains=search_query)
        )
    
    # Apply job filter
    if job_filter:
        all_candidates = all_candidates.filter(job_category=job_filter.upper())
    
    # Apply experience filter
    if exp_filter:
        if exp_filter == '0-2':
            all_candidates = all_candidates.filter(years_of_experience__gte=0, years_of_experience__lte=2)
        elif exp_filter == '3-5':
            all_candidates = all_candidates.filter(years_of_experience__gte=3, years_of_experience__lte=5)
        elif exp_filter == '6-10':
            all_candidates = all_candidates.filter(years_of_experience__gte=6, years_of_experience__lte=10)
        elif exp_filter == '10+':
            all_candidates = all_candidates.filter(years_of_experience__gte=10)
    
    # Apply age filter
    if age_filter:
        today = date.today()
        if age_filter == '18-25':
            min_birth = today - timedelta(days=25*365.25)
            max_birth = today - timedelta(days=18*365.25)
            all_candidates = all_candidates.filter(date_of_birth__gte=min_birth, date_of_birth__lte=max_birth)
        elif age_filter == '26-35':
            min_birth = today - timedelta(days=35*365.25)
            max_birth = today - timedelta(days=26*365.25)
            all_candidates = all_candidates.filter(date_of_birth__gte=min_birth, date_of_birth__lte=max_birth)
        elif age_filter == '36-45':
            min_birth = today - timedelta(days=45*365.25)
            max_birth = today - timedelta(days=36*365.25)
            all_candidates = all_candidates.filter(date_of_birth__gte=min_birth, date_of_birth__lte=max_birth)
        elif age_filter == '46-55':
            min_birth = today - timedelta(days=55*365.25)
            max_birth = today - timedelta(days=46*365.25)
            all_candidates = all_candidates.filter(date_of_birth__gte=min_birth, date_of_birth__lte=max_birth)
        elif age_filter == '55+':
            max_birth = today - timedelta(days=55*365.25)
            all_candidates = all_candidates.filter(date_of_birth__lte=max_birth)
    
    # Apply religion filter
    if religion_filter:
        all_candidates = all_candidates.filter(religion=religion_filter.upper())
    
    # Apply status filter
    if status_filter:
        all_candidates = all_candidates.filter(application_status=status_filter.upper())
    
    # Apply health filter
    if health_filter:
        all_candidates = all_candidates.filter(health_status=health_filter.upper())
    
    # STATS COUNTS (unfiltered totals for stats cards)
    total_candidates = Candidate.objects.count()
    available_count = Candidate.objects.filter(application_status='AVA').count()
    selected_count = Candidate.objects.filter(application_status='SEL').count()
    reserved_count = Candidate.objects.filter(application_status='RES').count()
    visa_count = Candidate.objects.filter(application_status='VIS').count()
    
    # IMPORTANT: Pass 'candidates' to the template
    context = {
        'candidates': all_candidates,  # ← This is what the template expects
        'total_candidates': total_candidates,
        'available_count': available_count,
        'selected_count': selected_count,
        'reserved_count': reserved_count,
        'visa_count': visa_count,
    }
    return render(request, 'recruitment/candidates_table.html', context)
from django.contrib.auth.models import User

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def manage_admin_users(request):
    """View to manage admin users (staff and superusers)"""
    # Exclude current user from the list
    admins = User.objects.filter(is_staff=True).exclude(id=request.user.id)
    return render(request, 'recruitment/manage_admin_users.html', {'admins': admins})

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def create_admin_user(request):
    """Create a new admin user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'recruitment/create_admin_user.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'recruitment/create_admin_user.html')
        
        # Create user
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password
        )
        user.is_staff = True
        user.is_superuser = is_superuser
        user.save()
        
        messages.success(request, f'Admin user "{username}" created successfully!')
        return redirect('manage_admin_users')
    
    return render(request, 'recruitment/create_admin_user.html')

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def delete_admin_user(request, user_id):
    """Delete an admin user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id, is_staff=True)
        
        # Prevent deleting yourself
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('manage_admin_users')
        
        username = user.username
        user.delete()
        messages.success(request, f'Admin user "{username}" has been deleted.')
        return redirect('manage_admin_users')
    
    return redirect('manage_admin_users')
@login_required(login_url='/client-login/')
@csrf_exempt
def cancel_booking(request):
    """Client cancels a booking - returns candidate to available status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Delete the booking
            ClientSelection.objects.filter(
                client=request.user,
                candidate=candidate,
                is_booked=True
            ).delete()
            
            # Check if candidate has any other selections/bookings
            if not ClientSelection.objects.filter(candidate=candidate).exists():
                candidate.application_status = 'AVA'
                candidate.save()
            
            return JsonResponse({'success': True, 'message': 'Booking cancelled successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def admin_reserved(request):
    """View all reserved/booked candidates with sponsor details"""
    # Get all candidates with status RESERVED (RES)
    reserved_candidates = Candidate.objects.filter(application_status='RES').order_by('-updated_at')
    
    # Get booking details for each reserved candidate
    bookings = ClientSelection.objects.filter(
        candidate__application_status='RES',
        is_booked=True
    ).select_related('client', 'candidate')
    
    context = {
        'reserved_candidates': reserved_candidates,
        'bookings': bookings,
        'total_count': reserved_candidates.count(),
    }
    return render(request, 'recruitment/admin_reserved.html', context)

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
def admin_visa_issued(request):
    """View all visa issued candidates (status = VIS)"""
    # Get all candidates with application_status = 'VIS' (Visa Issued)
    visa_candidates = Candidate.objects.filter(application_status='VIS').order_by('-updated_at')
    
    # Create a list with combined candidate and booking data
    candidate_data = []
    for candidate in visa_candidates:
        booking = ClientSelection.objects.filter(
            candidate=candidate,
            is_booked=True
        ).first()
        candidate_data.append({
            'candidate': candidate,
            'booking': booking
        })
    
    context = {
        'candidate_data': candidate_data,
        'total_count': visa_candidates.count(),
    }
    return render(request, 'recruitment/admin_visa_issued.html', context)

@login_required(login_url='/client-login/')
@csrf_exempt
def confirm_selection(request):
    """Client confirms a booking with sponsor details - changes status to SELECTED"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidate_id = data.get('candidate_id')
            sponsor_name = data.get('sponsor_name')
            sponsor_address = data.get('sponsor_address')
            sponsor_contact = data.get('sponsor_contact')
            sponsor_email = data.get('sponsor_email')
            booking_notes = data.get('booking_notes', '')
            
            candidate = get_object_or_404(Candidate, id=candidate_id)
            
            # Update selection with sponsor details and mark as confirmed
            selection, created = ClientSelection.objects.update_or_create(
                client=request.user,
                candidate=candidate,
                defaults={
                    'sponsor_name': sponsor_name,
                    'sponsor_address': sponsor_address,
                    'sponsor_contact': sponsor_contact,
                    'sponsor_email': sponsor_email,
                    'booking_notes': booking_notes,
                    'is_booked': False,
                    'is_confirmed': True
                }
            )
            
            # Update candidate status to SELECTED
            candidate.application_status = 'SEL'
            candidate.save()
            
            return JsonResponse({'success': True, 'message': 'Selection confirmed'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required(login_url='/admin/login/')
@user_passes_test(is_admin_user)
@csrf_exempt
def update_candidate_inline(request, pk):
    if request.method == 'POST':
        try:
            candidate = get_object_or_404(Candidate, pk=pk)
            
            # Handle JSON data (text fields)
            json_data = json.loads(request.POST.get('json_data', '{}'))
            
            # Update text fields
            for key, value in json_data.items():
                if hasattr(candidate, key):
                    if key in ['date_of_birth', 'passport_issue_date', 'passport_expiry_date']:
                        if value:
                            from datetime import datetime
                            setattr(candidate, key, datetime.strptime(value, '%Y-%m-%d').date())
                    elif key == 'years_of_experience':
                        setattr(candidate, key, int(value) if value else 0)
                    else:
                        setattr(candidate, key, value if value else '')
            
            # Handle file uploads (including video)
            file_fields = ['profile_photo', 'cv_pdf', 'passport_copy', 'visa_document', 
                          'medical_certificate', 'training_certificates', 'candidate_video']
            
            for field in file_fields:
                if field in request.FILES:
                    setattr(candidate, field, request.FILES[field])
            
            candidate.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})