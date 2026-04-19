# students/utils.py
import pandas as pd
from datetime import datetime
from django.db import transaction, IntegrityError
from .models import (
    Student, Attendance, AcademicPerformance, 
    NonAcademicPerformance, Subject, ExamType, DataUploadLog
)

class ExcelDataProcessor:
    """Handles processing of uploaded Excel files with auto-student creation"""
    
    def __init__(self, user):
        self.user = user
        self.errors = []
        self.success_count = 0
        self.failed_count = 0
        self.students_created = 0
    
    def get_or_create_student(self, roll_number, class_obj, row=None):
        """
        Get existing student or create new one from row data
        If student doesn't exist, creates with basic info or defaults
        """
        # Build student_data from row/defaults
        student_data = {
            'roll_number': roll_number,
            'student_class': class_obj,
            'is_active': True
        }

        # Try to extract name from row if available
        if row is not None:
            if 'student_name' in row:
                names = str(row['student_name']).split(' ', 1)
                student_data['first_name'] = names[0]
                student_data['last_name'] = names[1] if len(names) > 1 else ''
            elif 'first_name' in row and 'last_name' in row:
                student_data['first_name'] = row['first_name']
                student_data['last_name'] = row['last_name']
            else:
                # Default names based on roll number
                student_data['first_name'] = f'Student'
                student_data['last_name'] = roll_number

            # Optional fields
            if 'date_of_birth' in row or 'dob' in row:
                dob_str = row.get('date_of_birth') or row.get('dob')
                try:
                    if isinstance(dob_str, str):
                        student_data['date_of_birth'] = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    else:
                        student_data['date_of_birth'] = dob_str
                except:
                    student_data['date_of_birth'] = datetime(2010, 1, 1).date()  # Default
            else:
                student_data['date_of_birth'] = datetime(2010, 1, 1).date()

            if 'gender' in row:
                student_data['gender'] = row['gender']
            else:
                student_data['gender'] = 'Male'  # Default
        else:
            # No row data, use defaults
            student_data['first_name'] = 'Student'
            student_data['last_name'] = roll_number
            student_data['date_of_birth'] = datetime(2010, 1, 1).date()
            student_data['gender'] = 'Male'

        # Use get_or_create to avoid duplicate roll_number unique constraint errors
        try:
            student, created = Student.objects.get_or_create(
                roll_number=roll_number,
                defaults=student_data
            )
            if created:
                self.students_created += 1
            return student, created
        except IntegrityError:
            # Another process/row likely created the student concurrently — fetch existing and continue
            try:
                student = Student.objects.get(roll_number=roll_number)
                return student, False
            except Student.DoesNotExist:
                # Re-raise if we truly can't resolve
                raise
    
    def process_attendance_file(self, file, class_obj):
        """
        Process attendance Excel file
        Expected columns: roll_number, date, status, remarks (optional)
        Optional columns: student_name, first_name, last_name, gender, date_of_birth
        """
        try:
            df = pd.read_excel(file, engine='openpyxl')
            
            # Validate required columns
            required_cols = ['roll_number', 'date', 'status']
            if not all(col in df.columns for col in required_cols):
                self.errors.append(f"Missing required columns. Expected: {required_cols}")
                return False
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Get or create student
                        student, created = self.get_or_create_student(
                            str(row['roll_number']), 
                            class_obj, 
                            row
                        )
                        
                        if created:
                            self.errors.append(f"Row {index+2}: Created new student {student.roll_number}")
                        
                        # Parse date
                        if isinstance(row['date'], str):
                            date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                        else:
                            date = row['date']
                        
                        # Create or update attendance
                        Attendance.objects.update_or_create(
                            student=student,
                            date=date,
                            defaults={
                                'status': row['status'],
                                'remarks': row.get('remarks', ''),
                                'uploaded_by': self.user
                            }
                        )
                        self.success_count += 1
                        
                    except Exception as e:
                        self.errors.append(f"Row {index+2}: {str(e)}")
                        self.failed_count += 1
            
            # Log the upload
            self._log_upload('attendance', file.name)
            return True
            
        except Exception as e:
            self.errors.append(f"File processing error: {str(e)}")
            return False
    
    def process_academic_file(self, file, class_obj):
        """
        Process academic performance Excel file
        Expected columns: roll_number, subject_code, subject_name, exam_type, 
                         marks_obtained, max_marks, exam_date
        Optional: student_name, first_name, last_name
        """
        try:
            df = pd.read_excel(file, engine='openpyxl')
            
            required_cols = ['roll_number', 'subject_code', 'subject_name', 
                           'exam_type', 'marks_obtained', 'max_marks', 'exam_date']
            if not all(col in df.columns for col in required_cols):
                self.errors.append(f"Missing required columns. Expected: {required_cols}")
                return False
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Get or create subject
                        subject, _ = Subject.objects.get_or_create(
                            code=row['subject_code'],
                            defaults={'name': row['subject_name']}
                        )
                        
                        # Get or create exam type
                        exam_type, _ = ExamType.objects.get_or_create(
                            name=row['exam_type'],
                            defaults={'weightage': 25}  # Default weightage
                        )
                        
                        # Get or create student
                        student, created = self.get_or_create_student(
                            str(row['roll_number']), 
                            class_obj, 
                            row
                        )
                        
                        if created:
                            self.errors.append(f"Row {index+2}: Created new student {student.roll_number}")
                        
                        # Parse date
                        if isinstance(row['exam_date'], str):
                            exam_date = datetime.strptime(row['exam_date'], '%Y-%m-%d').date()
                        else:
                            exam_date = row['exam_date']
                        
                        # Create or update academic record
                        AcademicPerformance.objects.update_or_create(
                            student=student,
                            subject=subject,
                            exam_type=exam_type,
                            defaults={
                                'marks_obtained': row['marks_obtained'],
                                'max_marks': row['max_marks'],
                                'exam_date': exam_date,
                                'uploaded_by': self.user
                            }
                        )
                        self.success_count += 1
                        
                    except Exception as e:
                        self.errors.append(f"Row {index+2}: {str(e)}")
                        self.failed_count += 1
            
            self._log_upload('academic', file.name)
            return True
            
        except Exception as e:
            self.errors.append(f"File processing error: {str(e)}")
            return False
    
    def process_non_academic_file(self, file, class_obj):
        """
        Process non-academic performance Excel file
        Expected columns: roll_number, sports_participation, arts_creativity,
                         leadership_skills, teamwork, communication_skills,
                         discipline, punctuality, peer_relationships,
                         assessment_period
        Optional: student_name, extracurricular_participation, overall_conduct
        """
        try:
            df = pd.read_excel(file, engine='openpyxl')
            
            required_cols = ['roll_number', 'sports_participation', 'arts_creativity',
                           'leadership_skills', 'teamwork', 'communication_skills',
                           'discipline', 'punctuality', 'peer_relationships',
                           'assessment_period']
            if not all(col in df.columns for col in required_cols):
                self.errors.append(f"Missing required columns. Expected: {required_cols}")
                return False
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Get or create student
                        student, created = self.get_or_create_student(
                            str(row['roll_number']), 
                            class_obj, 
                            row
                        )
                        
                        if created:
                            self.errors.append(f"Row {index+2}: Created new student {student.roll_number}")
                        
                        # Create or update non-academic record
                        NonAcademicPerformance.objects.update_or_create(
                            student=student,
                            assessment_period=row['assessment_period'],
                            defaults={
                                'sports_participation': row['sports_participation'],
                                'arts_creativity': row['arts_creativity'],
                                'leadership_skills': int(row['leadership_skills']),
                                'teamwork': int(row['teamwork']),
                                'communication_skills': int(row['communication_skills']),
                                'discipline': row['discipline'],
                                'punctuality': int(row['punctuality']),
                                'peer_relationships': row['peer_relationships'],
                                'extracurricular_participation': row.get('extracurricular_participation', ''),
                                'overall_conduct': row.get('overall_conduct', ''),
                                'uploaded_by': self.user
                            }
                        )
                        self.success_count += 1
                        
                    except Exception as e:
                        self.errors.append(f"Row {index+2}: {str(e)}")
                        self.failed_count += 1
            
            self._log_upload('non_academic', file.name)
            return True
            
        except Exception as e:
            self.errors.append(f"File processing error: {str(e)}")
            return False
    
    def _log_upload(self, upload_type, file_name):
        """Log the upload activity"""
        status = 'success' if self.failed_count == 0 else ('partial' if self.success_count > 0 else 'failed')
        
        DataUploadLog.objects.create(
            upload_type=upload_type,
            file_name=file_name,
            uploaded_by=self.user,
            records_processed=self.success_count,
            records_failed=self.failed_count,
            status=status,
            error_log='\n'.join(self.errors)
        )
    
    def get_summary(self):
        """Return processing summary"""
        return {
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'students_created': self.students_created,
            'errors': self.errors
        }