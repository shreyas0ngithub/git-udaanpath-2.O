from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from students.models import Student
from students.views import calculate_predictions # Reusing your existing logic
from .utils import generate_ai_study_plan, generate_career_paths

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
    
from django.shortcuts import redirect
from django.contrib import messages

@login_required
@require_POST
def generate_career_api(request, student_id):
    """Fallback standard form submission to generate AI career suggestions"""
    student = get_object_or_404(Student, id=student_id)
    
    if not (hasattr(request.user, 'user_type') and request.user.user_type == 'parent' and student.parent == request.user):
        messages.error(request, 'Permission denied.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
        
    try:
        predictions = calculate_predictions(student)
        # Generate and save the AI response to the database
        generate_career_paths(student, predictions)
        
        # Send a success message to the frontend
        messages.success(request, f'Career paths successfully generated for {student.first_name}!')
        
    except Exception as e:
        messages.error(request, f'AI Engine Error: {str(e)}')
        
    # Simply reload the page. The dashboard template will automatically load the new data!
    return redirect(request.META.get('HTTP_REFERER', '/'))

# @login_required
# @require_POST
# def generate_career_api(request, student_id):
#     """API endpoint to generate AI career suggestions"""
#     student = get_object_or_404(Student, id=student_id)
    
#     if not (hasattr(request.user, 'user_type') and request.user.user_type == 'parent' and student.parent == request.user):
#         return JsonResponse({'error': 'Permission denied.'}, status=403)
        
#     try:
#         predictions = calculate_predictions(student)
#         rec = generate_career_paths(student, predictions)
        
#         return JsonResponse({
#             'status': 'success',
#             'html_content': rec.recommendation_html,
#             'generated_date': rec.generated_date.strftime("%B %d, %Y")
#         })
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)