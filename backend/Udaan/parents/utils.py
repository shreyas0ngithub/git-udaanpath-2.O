import os
import environ
import google.generativeai as genai
from students.models import StudyPlan, NonAcademicPerformance

env = environ.Env()
environ.Env.read_env()

genai.configure(api_key="AIzaSyBKrTUvrPoE1G4yeJ220M0fTek0WGEioFU") 

def generate_ai_study_plan(student, predictions_data):
    """
    Generates a personalized study plan using student analytics and the Gemini API.
    """
    weak_subject = predictions_data.get('recommended_focus', 'General Revision')
    strong_subject = predictions_data.get('strength_area', 'All Subjects')
    
    latest_behavior = NonAcademicPerformance.objects.filter(student=student).order_by('-uploaded_at').first()
    discipline_level = latest_behavior.discipline if latest_behavior else 'Average'
    
    system_prompt = f"""
    You are an expert educational AI tutor. Generate a 7-day after-school study plan.
    
    STUDENT CONTEXT:
    - Primary Focus (Weakest Subject): {weak_subject}
    - Strongest Subject: {strong_subject}
    - Discipline Level: {discipline_level}
    
    RULES FOR GENERATION:
    1. If Discipline is 'NeedsImprovement' or 'Average', break study blocks into short 25-minute Pomodoro sessions.
    2. If Discipline is 'Good' or 'Excellent', use longer 45-60 minute deep-work blocks.
    3. Allocate 50% of the total weekly study time to improving {weak_subject}.
    4. Allocate 15% of the time to maintaining {strong_subject}.
    5. Keep Sunday as a light review or rest day.
    
    OUTPUT FORMAT:
    Return ONLY clean, semantic HTML using Bootstrap classes. Do not include markdown block formatting (like ```html).
    Use a structured format like:
    <div class="mb-3">
        <h6 class="fw-bold text-primary">Monday</h6>
        <ul class="list-group list-group-flush small border rounded">
            <li class="list-group-item">...</li>
        </ul>
    </div>
    """

    # model = genai.GenerativeModel('gemini-1.5-flash-latest')
    model = genai.GenerativeModel('gemini-2.5-flash')
    # model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(system_prompt)
    generated_html = response.text.strip()
    
    if generated_html.startswith('```html'):
        generated_html = generated_html.replace('```html', '', 1)
    if generated_html.endswith('```'):
        generated_html = generated_html.rsplit('```', 1)[0]
    
    StudyPlan.objects.filter(student=student, is_active=True).update(is_active=False)
    
    new_plan = StudyPlan.objects.create(
        student=student,
        focus_subject=weak_subject,
        plan_content=generated_html.strip()
    )
    
    return new_plan