from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_redirect, name='home'),
    
    # Admin Authentication
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Candidate Management
    path('candidate/create/', views.candidate_create, name='candidate_create'),
    path('candidate/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidate/<int:pk>/edit/', views.candidate_update, name='candidate_update'),
    path('candidate/<int:pk>/delete/', views.delete_candidate, name='delete_candidate'),
    path('place-candidate/', views.place_candidate, name='place_candidate'),
    path('mass-delete-candidates/', views.mass_delete_candidates, name='mass_delete_candidates'),
    
    # Client Portal
    path('client-portal/', views.client_portal, name='client_portal'),
    path('client/candidate/<int:pk>/', views.client_candidate_detail, name='client_candidate_detail'),
    
    # Client Authentication
    path('client-register/', views.client_register, name='client_register'),
    path('client-login/', views.client_login_view, name='client_login'),
    path('client-logout/', views.client_logout_view, name='client_logout'),
    
    # Client Management
    path('manage-clients/', views.manage_clients, name='manage_clients'),
    path('create-client/', views.create_client_user, name='create_client'),
    path('toggle-client/<int:user_id>/', views.toggle_client_status, name='toggle_client_status'),
    path('reset-client-pw/<int:user_id>/', views.reset_client_password, name='reset_client_password'),
    path('delete-client/<int:user_id>/', views.delete_client, name='delete_client'),

    path('toggle-select-candidate/', views.toggle_select_candidate, name='toggle_select_candidate'),
path('client-selections/', views.client_selections, name='client_selections'),
path('admin-selections/', views.admin_selections, name='admin_selections'),

# Admin User Management
path('manage-admin-users/', views.manage_admin_users, name='manage_admin_users'),
path('create-admin-user/', views.create_admin_user, name='create_admin_user'),
path('toggle-admin-status/<int:user_id>/', views.toggle_admin_status, name='toggle_admin_status'),
path('reset-admin-password/<int:user_id>/', views.reset_admin_password, name='reset_admin_password'),
path('delete-admin-user/<int:user_id>/', views.delete_admin_user, name='delete_admin_user'),
]