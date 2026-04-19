from django.contrib import admin

# Register your models here.
# students/admin.py
from django.contrib import admin
from .models import (
    Class, Student, Subject, Attendance, 
    ExamType, AcademicPerformance, NonAcademicPerformance, DataUploadLog
)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['grade', 'section', 'academic_year', 'teacher']
    list_filter = ['grade', 'academic_year']
    search_fields = ['grade', 'section', 'teacher__username']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_number', 'first_name', 'last_name', 'student_class', 'is_active']
    list_filter = ['student_class', 'gender', 'is_active']
    search_fields = ['roll_number', 'first_name', 'last_name']
    date_hierarchy = 'enrollment_date'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']

@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'weightage']
    search_fields = ['name']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'uploaded_by']
    list_filter = ['status', 'date']
    search_fields = ['student__roll_number', 'student__first_name']
    date_hierarchy = 'date'

@admin.register(AcademicPerformance)
class AcademicPerformanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'exam_type', 'marks_obtained', 'max_marks', 'percentage']
    list_filter = ['exam_type', 'subject']
    search_fields = ['student__roll_number', 'student__first_name']
    date_hierarchy = 'exam_date'
    
    def percentage(self, obj):
        return f"{obj.percentage:.2f}%"

@admin.register(NonAcademicPerformance)
class NonAcademicPerformanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment_period', 'discipline', 'leadership_skills', 'teamwork']
    list_filter = ['assessment_period', 'discipline']
    search_fields = ['student__roll_number', 'student__first_name']

@admin.register(DataUploadLog)
class DataUploadLogAdmin(admin.ModelAdmin):
    list_display = ['upload_type', 'file_name', 'uploaded_by', 'uploaded_at', 'status', 'records_processed']
    list_filter = ['upload_type', 'status', 'uploaded_at']
    search_fields = ['file_name', 'uploaded_by__username']
    date_hierarchy = 'uploaded_at'
    readonly_fields = ['uploaded_at']