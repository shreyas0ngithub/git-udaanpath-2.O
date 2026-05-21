import os
import environ
import google.generativeai as genai
from students.models import StudyPlan, NonAcademicPerformance
from students.models import CareerRecommendation

env = environ.Env()
environ.Env.read_env()

genai.configure(api_key="AIzaSyDROqc2lTy9M4HJoRNCgZlCU-X7KJv8RXQ") 

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



def generate_career_paths(student, predictions_data):
    """
    Feeds holistic student data to Gemini to suggest future career paths.
    """
    strong_subject = predictions_data.get('strength_area', 'General Studies')
    weak_subject = predictions_data.get('recommended_focus', 'None')
    
    # Grab the latest soft-skills data
    latest_behavior = NonAcademicPerformance.objects.filter(student=student).order_by('-uploaded_at').first()
    
    leadership = latest_behavior.leadership_skills if latest_behavior else 'Average'
    communication = latest_behavior.communication_skills if latest_behavior else 'Average'
    teamwork = latest_behavior.teamwork if latest_behavior else 'Average'

    system_prompt = f"""
    You are an expert high school career counselor and life coach.
    Based on the student's academic and behavioral data, suggest 3 highly specific, modern career paths.
    
    STUDENT PROFILE:
    - Academic Strength: {strong_subject}
    - Academic Weakness: {weak_subject}
    - Soft Skills: Leadership ({leadership}/5), Communication ({communication}/5), Teamwork ({teamwork}/5).
    
    For each career path, explain WHY it fits their profile, and give 2 concrete "Next Steps" they can do right now (e.g., clubs to join, hobbies, basic skills to learn) to explore this interest.
    
    OUTPUT FORMAT:
    Return ONLY clean, semantic HTML using Bootstrap 5 classes. No markdown wrappers.
    Use this exact structure for each of the 3 careers:
    <div class="mb-4 border-start border-4 border-success ps-3">
        <h5 class="fw-bold text-dark">[Career Title]</h5>
        <p class="text-muted small"><strong>Why it fits:</strong> [Explain connection to their specific subjects and soft skills]</p>
        <p class="mb-1 fw-bold text-success" style="font-size: 0.85rem;">Actionable Next Steps:</p>
        <ul class="small text-muted">
            <li>[Step 1]</li>
            <li>[Step 2]</li>
        </ul>
    </div>
    """

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(system_prompt)
    generated_html = response.text.strip()
    
    # Clean up markdown if accidentally added
    if generated_html.startswith('```html'):
        generated_html = generated_html.replace('```html', '', 1)
    if generated_html.endswith('```'):
        generated_html = generated_html.rsplit('```', 1)[0]
    
    # Deactivate old recommendations and save the new one
    CareerRecommendation.objects.filter(student=student, is_active=True).update(is_active=False)
    
    new_recommendation = CareerRecommendation.objects.create(
        student=student,
        recommendation_html=generated_html.strip()
    )
    
    return new_recommendation