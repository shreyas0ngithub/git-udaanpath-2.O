from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.urls import reverse
from .forms import (
    SchoolRegistrationForm, 
    TeacherRegistrationForm, 
    ParentRegistrationForm, 
    CustomLoginForm,
    SchoolLoginForm
)
from .models import School, Teacher, Parent, CustomUser
from students.models import Student

def home(request):
    """Home page with login/registration options"""
    return render(request, 'authentication/home.html')

# School Views
@csrf_protect
def school_register(request):
    """School registration view"""
    if request.method == 'POST':
        form = SchoolRegistrationForm(request.POST)
        if form.is_valid():
            school = form.save()
            messages.success(request, f'School "{school.school_name}" registered successfully!')
            return redirect('authentication:school_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SchoolRegistrationForm()
    
    return render(request, 'authentication/school_register.html', {'form': form})

@csrf_protect
def school_login(request):
    """School login view"""
    if request.method == 'POST':
        form = SchoolLoginForm(request.POST)
        if form.is_valid():
            school = form.cleaned_data['school']
            # Store school info in session for school admin dashboard
            request.session['school_id'] = school.id
            request.session['school_name'] = school.school_name
            request.session['user_type'] = 'school'
            messages.success(request, f'Welcome, {school.school_name}!')
            return redirect('authentication:school_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = SchoolLoginForm()
    
    return render(request, 'authentication/school_login.html', {'form': form})

def school_dashboard(request):
    """School dashboard view"""
    if 'school_id' not in request.session:
        messages.error(request, 'Please login first.')
        return redirect('authentication:school_login')
    
    school_id = request.session['school_id']
    school = School.objects.get(id=school_id)
    teachers = Teacher.objects.filter(school=school, is_active=True)
    
    context = {
        'school': school,
        'teachers': teachers,
        'teacher_count': teachers.count(),
    }
    return render(request, 'authentication/school_dashboard.html', context)

# Teacher Views
@csrf_protect
def teacher_register(request):
    """Teacher registration view"""
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher "{teacher.teacher_name}" registered successfully!')
            return redirect('authentication:teacher_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherRegistrationForm()
    
    return render(request, 'authentication/teacher_register.html', {'form': form})

@csrf_protect
def teacher_login(request):
    """Teacher login view"""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.user_type == 'teacher':
                login(request, user)
                messages.success(request, f'Welcome, {user.teacher.teacher_name}!')
                return redirect('students:welcome_intro')
            else:
                messages.error(request, 'Invalid user type for teacher login.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = CustomLoginForm()

    return render(request, 'authentication/teacher_login.html', {'form': form})

@login_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    if request.user.user_type != 'teacher':
        messages.error(request, 'Access denied.')
        return redirect('authentication:home')
    
    teacher = request.user.teacher
    context = {
        'teacher': teacher,
        'school': teacher.school,
    }
    return render(request, 'authentication/teacher_dashboard.html', context)

# Parent Views
@csrf_protect
def parent_register(request):
    """Parent registration view"""
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            parent = form.save()
            messages.success(request, 'Parent registration successful! Please wait for verification.')
            return redirect('authentication:parent_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ParentRegistrationForm()
    
    return render(request, 'authentication/parent_register.html', {'form': form})

@csrf_protect
def parent_login(request):
    """Parent login view"""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.user_type == 'parent':
                if user.parent.is_verified:
                    login(request, user)
                    messages.success(request, f'Welcome, Parent of {user.parent.child_name}!')
                    return redirect('authentication:parent_dashboard')
                else:
                    messages.error(request, 'Your account is not verified yet. Please contact the school.')
            else:
                messages.error(request, 'Invalid user type for parent login.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'authentication/parent_login.html', {'form': form})

@login_required
def parent_dashboard(request):
    """Parent dashboard view"""
    if request.user.user_type != 'parent':
        messages.error(request, 'Access denied.')
        return redirect('authentication:home')
    
    parent = request.user.parent
    # amazonq-ignore-next-line
    student = Student.objects.get(date_of_birth=parent.child_dob)  # Assuming child_dob uniquely identifies the student
    student_id = student.pk

    context = {
        'parent': parent,
        'student_id' : student_id,
        'child_name': parent.child_name,
        'child_class': parent.get_child_class_display(),
        'child_section': parent.get_child_section_display(),
    }
    return render(request, 'authentication/parent_dashboard.html', context)

# Common Views
def custom_logout(request):
    """Logout view for all user types"""
    # Clear school session if exists
    if 'school_id' in request.session:
        del request.session['school_id']
        del request.session['school_name']
        del request.session['user_type']
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('authentication:home')

def user_profile(request):
    """User profile view"""
    if request.user.is_authenticated:
        context = {}
        if request.user.user_type == 'teacher':
            context['profile'] = request.user.teacher
        elif request.user.user_type == 'parent':
            context['profile'] = request.user.parent
        
        return render(request, 'authentication/user_profile.html', context)
    else:
        messages.error(request, 'Please login first.')
        return redirect('authentication:home')

# AJAX Views for dynamic content
def get_schools_ajax(request):
    """Get list of schools for AJAX requests"""
    schools = School.objects.filter(is_active=True).values('id', 'school_name')
    return JsonResponse({'schools': list(schools)})

def verify_child_data(request):
    """
    This view will be used to verify parent registration against uploaded Excel data
    Implementation will depend on the student data management app
    For now, it's a placeholder
    """
    if request.method == 'POST':
        # This would verify against uploaded Excel data
        # Implementation depends on the student management app
        pass
    
    return JsonResponse({'status': 'pending'})