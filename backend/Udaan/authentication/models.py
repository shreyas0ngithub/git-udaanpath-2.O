# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        # Auto-generate username from email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'teacher')  # Default for admin
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class School(models.Model):
    school_name = models.CharField(max_length=200)
    located_at = models.CharField(max_length=300)
    school_id = models.CharField(max_length=50, unique=True)
    principal_name = models.CharField(max_length=100)
    school_email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Will be hashed
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.school_name
    
    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('school', 'School Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    
    # Make username optional and use email as the unique identifier
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Use our custom manager
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_type']
    
    def save(self, *args, **kwargs):
        # Auto-generate username from email if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.email} ({self.get_user_type_display()})"

class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers')
    teacher_name = models.CharField(max_length=100)
    teacher_id = models.CharField(max_length=50)
    
    # Mobile number validator
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    mobile_number = models.CharField(validators=[phone_regex], max_length=17)
    
    # Class and section
    CLASS_CHOICES = [
        ('1', 'Class 1'), ('2', 'Class 2'), ('3', 'Class 3'), ('4', 'Class 4'),
        ('5', 'Class 5'), ('6', 'Class 6'), ('7', 'Class 7'), ('8', 'Class 8'),
        ('9', 'Class 9'), ('10', 'Class 10'), ('11', 'Class 11'), ('12', 'Class 12'),
    ]
    
    SECTION_CHOICES = [
        ('A', 'Section A'), ('B', 'Section B'), ('C', 'Section C'), 
        ('D', 'Section D'), ('E', 'Section E'),
    ]
    
    class_assigned = models.CharField(max_length=2, choices=CLASS_CHOICES)
    section_assigned = models.CharField(max_length=1, choices=SECTION_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.teacher_name} - {self.school.school_name}"
    
    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
        unique_together = ['school', 'teacher_id']

class Parent(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    child_name = models.CharField(max_length=100)
    
    CLASS_CHOICES = [
        ('1', 'Class 1'), ('2', 'Class 2'), ('3', 'Class 3'), ('4', 'Class 4'),
        ('5', 'Class 5'), ('6', 'Class 6'), ('7', 'Class 7'), ('8', 'Class 8'),
        ('9', 'Class 9'), ('10', 'Class 10'), ('11', 'Class 11'), ('12', 'Class 12'),
    ]
    
    SECTION_CHOICES = [
        ('A', 'Section A'), ('B', 'Section B'), ('C', 'Section C'), 
        ('D', 'Section D'), ('E', 'Section E'),
    ]
    
    child_class = models.CharField(max_length=2, choices=CLASS_CHOICES)
    child_section = models.CharField(max_length=1, choices=SECTION_CHOICES)
    child_dob = models.DateField()
    
    # This will be verified against uploaded Excel data
    is_verified = models.BooleanField(default=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Parent of {self.child_name}"
    
    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"