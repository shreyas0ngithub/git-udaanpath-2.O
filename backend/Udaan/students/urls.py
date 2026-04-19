# students/urls.py
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('intro/', views.welcome_intro, name='welcome_intro'),
    path('upload/', views.upload_data, name='upload_data'),
    path('list/', views.student_list, name='student_list'),


    path('student/<int:student_id>/', views.student_dashboard, name='student_dashboard'),

    path('class/<int:class_id>/analytics/', views.class_analytics, name='class_analytics'),
    
    path('api/student/<int:student_id>/chart-data/', views.get_student_chart_data, name='chart_data'),

    
    # Additional analytics endpoints
    path('api/student/<int:student_id>/predictions/', views.get_predictions, name='predictions_api'),
    path('api/student/<int:student_id>/performance-summary/', views.get_performance_summary, name='performance_summary'),
    path('api/class/<int:class_id>/statistics/', views.get_class_statistics, name='class_statistics'),
]