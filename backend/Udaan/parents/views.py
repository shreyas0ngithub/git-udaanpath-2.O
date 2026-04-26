from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from students.models import Student
from students.views import calculate_predictions # Reusing your existing logic
from .utils import generate_ai_study_plan

@login_required
def generate_study_plan_api(request, student_id):
    """API endpoint triggered by parents to generate an AI study plan"""
    student = get_object_or_404(Student, id=student_id)
    
    # Access Control: Ensure the logged-in user is actually this student's parent
    if not (hasattr(request.user, 'user_type') and request.user.user_type == 'parent' and student.parent == request.user):
        return JsonResponse({'error': 'Permission denied. You can only generate plans for your own child.'}, status=403)
        
    try:
        # Gather predictive context from the students app
        predictions = calculate_predictions(student)
        
        # Call the Gemini AI Utility
        plan = generate_ai_study_plan(student, predictions)
        
        return JsonResponse({
            'status': 'success',
            'focus_subject': plan.focus_subject,
            'plan_html': plan.plan_content,
            'generated_date': plan.generated_date.strftime("%B %d, %Y")
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)