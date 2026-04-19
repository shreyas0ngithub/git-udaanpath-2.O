from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from .models import School, Teacher, Parent, CustomUser

class SchoolRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
    )
    
    class Meta:
        model = School
        fields = ['school_name', 'located_at', 'school_id', 'principal_name', 'school_email', 'password']
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter school name'}),
            'located_at': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'school_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter unique school ID'}),
            'principal_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter principal name'}),
            'school_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter school email'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        school = super().save(commit=False)
        # Hash the password before saving
        school.password = make_password(self.cleaned_data['password'])
        if commit:
            school.save()
        return school

class TeacherRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    
    class Meta:
        model = Teacher
        fields = ['school', 'teacher_name', 'teacher_id', 'mobile_number', 'class_assigned', 'section_assigned']
        widgets = {
            'school': forms.Select(attrs={'class': 'form-control'}),
            'teacher_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter teacher name'}),
            'teacher_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter teacher ID'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'class_assigned': forms.Select(attrs={'class': 'form-control'}),
            'section_assigned': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active schools in the dropdown
        self.fields['school'].queryset = School.objects.filter(is_active=True)
        self.fields['school'].empty_label = "Select a school"
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        teacher = super().save(commit=False)
        
        # Create CustomUser instance
        user = CustomUser.objects.create_user(
            username=self.cleaned_data['teacher_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            user_type='teacher'
        )
        teacher.user = user
        
        if commit:
            teacher.save()
        return teacher

class ParentRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    
    class Meta:
        model = Parent
        fields = ['child_name', 'child_class', 'child_section', 'child_dob']
        widgets = {
            'child_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter child name'}),
            'child_class': forms.Select(attrs={'class': 'form-control'}),
            'child_section': forms.Select(attrs={'class': 'form-control'}),
            'child_dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError("Passwords don't match")
        
        return cleaned_data
    
    def save(self, commit=True):
        parent = super().save(commit=False)
        
        # Create CustomUser instance
        user = CustomUser.objects.create_user(
            username=self.cleaned_data['child_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            user_type='parent'
        )
        parent.user = user
        
        if commit:
            parent.save()
        return parent

class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'

class SchoolLoginForm(forms.Form):
    school_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter school email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        school_email = cleaned_data.get('school_email')
        password = cleaned_data.get('password')
        
        if school_email and password:
            try:
                from django.contrib.auth.hashers import check_password
                school = School.objects.get(school_email=school_email, is_active=True)
                if not check_password(password, school.password):
                    raise ValidationError("Invalid email or password")
                cleaned_data['school'] = school
            except School.DoesNotExist:
                raise ValidationError("Invalid email or password")
        
        return cleaned_data