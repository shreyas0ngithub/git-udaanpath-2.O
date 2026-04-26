from django.urls import path
from . import views

app_name = "school"

urlpatterns = [
    path("", views.index, name="index"),
    path("list/", views.school_list, name="school_list"),
    path("<int:pk>/", views.school_detail, name="school_detail"),
]