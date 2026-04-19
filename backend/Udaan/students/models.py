# students/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Class(models.Model):
    """Model for class/grade sections"""
    grade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    section = models.CharField(max_length=2)
    academic_year = models.CharField(max_length=9)  # e.g., "2024-2025"
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='classes_taught')
    
    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ['grade', 'section', 'academic_year']
    
    def __str__(self):
        return f"Class {self.grade}{self.section} ({self.academic_year})"


class Student(models.Model):
    """Core student information"""
    roll_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ])
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['roll_number']
    
    def __str__(self):
        return f"{self.roll_number} - {self.first_name} {self.last_name}"


class Subject(models.Model):
    """Subjects offered in school"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Attendance(models.Model):
    """Student attendance records"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Excused', 'Excused')
    ])
    remarks = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.date} - {self.status}"


class ExamType(models.Model):
    """Types of examinations"""
    name = models.CharField(max_length=50)  # ClassTest1, ClassTest2, MidTerm, EndTerm
    weightage = models.IntegerField(help_text="Weightage in percentage")
    
    def __str__(self):
        return self.name


class AcademicPerformance(models.Model):
    """Academic marks in various subjects"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='academic_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    exam_date = models.DateField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'exam_type']
        ordering = ['-exam_date']
    
    def __str__(self):
        return f"{self.student.roll_number} - {self.subject.code} - {self.exam_type.name}"
    
    @property
    def percentage(self):
        return (self.marks_obtained / self.max_marks) * 100 if self.max_marks > 0 else 0


class NonAcademicPerformance(models.Model):
    """Non-academic performance metrics"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='non_academic_records')
    
    # Sports and Physical Education
    sports_participation = models.CharField(max_length=20, choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('NeedsImprovement', 'Needs Improvement')
    ])
    
    # Arts and Creativity
    arts_creativity = models.CharField(max_length=20, choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('NeedsImprovement', 'Needs Improvement')
    ])
    
    # Leadership and Teamwork
    leadership_skills = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Communication
    communication_skills = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Behavior and Discipline
    discipline = models.CharField(max_length=20, choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('NeedsImprovement', 'Needs Improvement')
    ])
    punctuality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    # Social Skills
    peer_relationships = models.CharField(max_length=20, choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Average', 'Average'),
        ('NeedsImprovement', 'Needs Improvement')
    ])
    
    # Extra-curricular Activities
    extracurricular_participation = models.CharField(max_length=200, blank=True, help_text="Comma-separated activities")
    
    # Overall Behavior
    overall_conduct = models.TextField(blank=True)
    
    # Metadata
    assessment_period = models.CharField(max_length=50)  # e.g., "Term 1", "Term 2"
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'assessment_period']
    
    def __str__(self):
        return f"{self.student.roll_number} - Non-Academic ({self.assessment_period})"


class DataUploadLog(models.Model):
    """Track all data uploads"""
    upload_type = models.CharField(max_length=20, choices=[
        ('attendance', 'Attendance'),
        ('academic', 'Academic Performance'),
        ('non_academic', 'Non-Academic Performance')
    ])
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    records_processed = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed')
    ])
    error_log = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.upload_type} - {self.uploaded_at} - {self.status}"