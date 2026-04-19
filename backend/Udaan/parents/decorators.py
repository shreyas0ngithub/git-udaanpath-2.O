from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def parent_required(view_func):
    """Decorator to ensure user is a parent and is verified"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        # Check if user is a parent
        if request.user.user_type != 'parent':
            messages.error(request, 'Access denied. This page is only for parents.')
            return redirect('authentication:home')
        
        # Check if parent has a profile
        if not hasattr(request.user, 'parent'):
            messages.error(request, 'Parent profile not found. Please contact support.')
            return redirect('authentication:home')
        
        # Check if parent is verified
        if not request.user.parent.is_verified:
            messages.warning(request, 'Your account is not yet verified. Please wait for verification.')
            return redirect('parents:verification_pending')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def parent_owns_child(view_func):
    """Decorator to ensure parent can only access their child's data"""
    @wraps(view_func)
    def _wrapped_view(request, student_id=None, *args, **kwargs):
        from students.models import Student
        
        try:
            student = Student.objects.get(id=student_id)
            
            # Check if this student belongs to the logged-in parent
            if student.parent != request.user:
                messages.error(request, 'You do not have permission to view this student.')
                return redirect('parents:dashboard')
            
            # Add student to request for easy access
            request.student = student
            
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')
            return redirect('parents:dashboard')
        
        return view_func(request, student_id=student_id, *args, **kwargs)
    
    return _wrapped_view