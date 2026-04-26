from django.urls import path
from . import views

"""URL configuration for UdaanPath project."""

app_name = "parents"

urlpatterns = [

    path('api/student/<int:student_id>/generate-study-plan/', views.generate_study_plan_api, name='generate_study_plan')

]