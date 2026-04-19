# students/forms.py
from django import forms
from .models import Class

class DataUploadForm(forms.Form):
    """Form for uploading Excel files"""
    
    class_selection = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=True,
        label="Select Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    attendance_file = forms.FileField(
        required=False,
        label="Attendance Data (Excel)",
        help_text="Upload attendance records in .xlsx format",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    academic_file = forms.FileField(
        required=False,
        label="Academic Performance Data (Excel)",
        help_text="Upload academic marks in .xlsx format",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    non_academic_file = forms.FileField(
        required=False,
        label="Non-Academic Performance Data (Excel)",
        help_text="Upload non-academic assessments in .xlsx format",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only classes taught by this teacher
        # self.fields['class_selection'].queryset = Class.objects.filter(teacher=user)
        self.fields['class_selection'].queryset = Class.objects.all()

    
    def clean(self):
        cleaned_data = super().clean()
        attendance_file = cleaned_data.get('attendance_file')
        academic_file = cleaned_data.get('academic_file')
        non_academic_file = cleaned_data.get('non_academic_file')
        
        # At least one file must be uploaded
        if not any([attendance_file, academic_file, non_academic_file]):
            raise forms.ValidationError("Please upload at least one Excel file.")
        
        return cleaned_data


class StudentSearchForm(forms.Form):
    """Form for searching students"""
    search_query = forms.CharField(
        required=False,
        label="Search Student",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter roll number or name...'
        })
    )
    
    class_filter = forms.ModelChoiceField(
        queryset=Class.objects.all(),
        required=False,
        label="Filter by Class",
        widget=forms.Select(attrs={'class': 'form-control'})
    )