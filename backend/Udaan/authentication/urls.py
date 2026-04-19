from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # School URLs
    path('school/register/', views.school_register, name='school_register'),
    path('school/login/', views.school_login, name='school_login'),
    path('school/dashboard/', views.school_dashboard, name='school_dashboard'),
    
    # Teacher URLs
    path('teacher/register/', views.teacher_register, name='teacher_register'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    
    # Parent URLs
    path('parent/register/', views.parent_register, name='parent_register'),
    path('parent/login/', views.parent_login, name='parent_login'),
    path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
    
    # Common URLs
    path('logout/', views.custom_logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    
    # AJAX URLs
    path('ajax/schools/', views.get_schools_ajax, name='get_schools_ajax'),
    path('ajax/verify-child/', views.verify_child_data, name='verify_child_data'),
]