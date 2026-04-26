from django.shortcuts import render
from .models import School

# Create your views here.
def index(request):
    return render(request, "school/index.html")

def school_list(request):
    schools = School.objects.all()
    return render(request, "school/school_list.html", {"schools": schools})