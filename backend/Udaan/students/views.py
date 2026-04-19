from django.shortcuts import render

# Create your views here.
# students/views.py - Enhanced with Predictive Analytics

from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek
from django.http import JsonResponse
from datetime import datetime, timedelta
import statistics
from .models import Student, Class, Attendance, AcademicPerformance, NonAcademicPerformance
from .forms import DataUploadForm, StudentSearchForm
from .utils import ExcelDataProcessor



# views.py
def welcome_intro(request):
    return render(request, 'students/intro.html')

@login_required
def dashboard(request):
    """Main dashboard for teachers"""
    # Get classes taught by teacher
    classes = Class.objects.filter(teacher=request.user)
    
    # Get statistics
    total_students = Student.objects.filter(student_class__in=classes).count()
    
    context = {
        'classes': classes,
        'total_students': total_students,
    }
    return render(request, 'students/dashboard.html', context)


@login_required
def upload_data(request):
    """Handle Excel file uploads"""
    if request.method == 'POST':
        form = DataUploadForm(request.user, request.POST, request.FILES)
        
        if form.is_valid():
            class_obj = form.cleaned_data['class_selection']
            processor = ExcelDataProcessor(request.user)
            
            # Process each uploaded file
            results = []
            
            if form.cleaned_data.get('attendance_file'):
                file = request.FILES['attendance_file']
                success = processor.process_attendance_file(file, class_obj)
                results.append(('Attendance', success))
            
            if form.cleaned_data.get('academic_file'):
                file = request.FILES['academic_file']
                processor_academic = ExcelDataProcessor(request.user)
                success = processor_academic.process_academic_file(file, class_obj)
                results.append(('Academic', success))
            
            if form.cleaned_data.get('non_academic_file'):
                file = request.FILES['non_academic_file']
                processor_non_academic = ExcelDataProcessor(request.user)
                success = processor_non_academic.process_non_academic_file(file, class_obj)
                results.append(('Non-Academic', success))
            
            # Show results
            for data_type, success in results:
                if success:
                    messages.success(request, f'{data_type} data uploaded successfully!')
                else:
                    messages.error(request, f'Error uploading {data_type} data. Check logs for details.')
            
            # Show any errors
            all_processors = [processor]
            if form.cleaned_data.get('academic_file'):
                all_processors.append(processor_academic)
            if form.cleaned_data.get('non_academic_file'):
                all_processors.append(processor_non_academic)
            
            for proc in all_processors:
                summary = proc.get_summary()
                if summary['errors']:
                    for error in summary['errors'][:5]:  # Show first 5 errors
                        messages.warning(request, error)
            
            return redirect('students:upload_data')
    else:
        form = DataUploadForm(request.user)
    
    # Get recent uploads
    recent_uploads = request.user.datauploadlog_set.all()[:10]
    
    context = {
        'form': form,
        'recent_uploads': recent_uploads,
    }
    return render(request, 'students/upload_data.html', context)



@login_required
def student_list(request):
    """List all students with search and filter"""
    # Get classes taught by teacher
    classes = Class.objects.filter(teacher=request.user)
    students = Student.objects.filter(student_class__in=classes)
    
    # Apply search and filters
    form = StudentSearchForm(request.GET)
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        class_filter = form.cleaned_data.get('class_filter')
        
        if search_query:
            students = students.filter(
                Q(roll_number__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        if class_filter:
            students = students.filter(student_class=class_filter)
    
    context = {
        'students': students,
        'form': form,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def class_analytics(request, class_id):
    """Analytics for entire class"""
    class_obj = get_object_or_404(Class, id=class_id, teacher=request.user)
    students = class_obj.students.all()
    
    # Overall class statistics
    total_students = students.count()
    
    # Attendance statistics
    attendance_stats = Attendance.objects.filter(
        student__in=students
    ).aggregate(
        total_present=Count('id', filter=Q(status='Present')),
        total_absent=Count('id', filter=Q(status='Absent')),
    )
    
    # Academic statistics
    academic_avg = AcademicPerformance.objects.filter(
        student__in=students
    ).aggregate(Avg('marks_obtained'))
    
    context = {
        'class_obj': class_obj,
        'total_students': total_students,
        'attendance_stats': attendance_stats,
        'academic_avg': academic_avg,
    }
    return render(request, 'students/class_analytics.html', context)


def calculate_predictions(student):
    """
    Calculate predictive analytics for student performance
    """
    # Get all academic records
    academic_records = student.academic_records.all().order_by('exam_date')
    
    if not academic_records.exists():
        return {
            'predicted_score': 0,
            'success_probability': 0,
            'recommended_focus': 'N/A',
            'strength_area': 'N/A',
            'trend': 'stable'
        }
    
    # Calculate average scores over time
    scores = [float(record.percentage) for record in academic_records]
    
    # Simple linear regression for trend prediction
    if len(scores) >= 3:
        # Calculate trend
        x = list(range(len(scores)))
        mean_x = sum(x) / len(x)
        mean_y = sum(scores) / len(scores)
        
        numerator = sum((x[i] - mean_x) * (scores[i] - mean_y) for i in range(len(scores)))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        
        if denominator != 0:
            slope = numerator / denominator
            predicted_score = scores[-1] + (slope * 2)  # Predict 2 exams ahead
        else:
            predicted_score = scores[-1]
    else:
        predicted_score = sum(scores) / len(scores)
    
    # Ensure prediction is within valid range
    predicted_score = max(0, min(100, predicted_score))
    
    # Calculate success probability (based on consistency and average)
    if len(scores) > 1:
        std_dev = statistics.stdev(scores)
        avg_score = sum(scores) / len(scores)
        consistency_factor = 1 - (std_dev / 100)  # Lower std dev = higher consistency
        success_probability = (avg_score / 100) * 0.7 + consistency_factor * 0.3
        success_probability = min(99, max(50, success_probability * 100))
    else:
        success_probability = 75
    
    # Find weakest and strongest subjects
    subject_averages = {}
    for record in academic_records:
        subject_name = record.subject.name
        if subject_name not in subject_averages:
            subject_averages[subject_name] = []
        subject_averages[subject_name].append(float(record.percentage))
    
    subject_means = {
        subject: sum(scores) / len(scores) 
        for subject, scores in subject_averages.items()
    }
    
    if subject_means:
        recommended_focus = min(subject_means, key=subject_means.get)
        strength_area = max(subject_means, key=subject_means.get)
    else:
        recommended_focus = 'N/A'
        strength_area = 'N/A'
    
    # Determine trend
    if len(scores) >= 2:
        recent_avg = sum(scores[-3:]) / len(scores[-3:])
        overall_avg = sum(scores) / len(scores)
        if recent_avg > overall_avg + 5:
            trend = 'improving'
        elif recent_avg < overall_avg - 5:
            trend = 'declining'
        else:
            trend = 'stable'
    else:
        trend = 'stable'
    
    return {
        'predicted_score': round(predicted_score, 1),
        'success_probability': round(success_probability),
        'recommended_focus': recommended_focus,
        'strength_area': strength_area,
        'trend': trend,
        'improvement_needed': round(100 - subject_means.get(recommended_focus, 100), 1) if subject_means else 0
    }


def calculate_class_rank(student):
    """
    Calculate student's rank in class based on average performance
    """
    student_class = student.student_class
    students_in_class = student_class.students.all()
    
    # Calculate average for each student
    student_averages = []
    for s in students_in_class:
        avg = s.academic_records.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        if avg:
            student_averages.append((s.id, avg))
    
    if not student_averages:
        return 'N/A', 0
    
    # Sort by average (descending)
    student_averages.sort(key=lambda x: x[1], reverse=True)
    
    # Find student's rank
    for rank, (student_id, avg) in enumerate(student_averages, 1):
        if student_id == student.id:
            total_students = len(student_averages)
            percentile = (1 - (rank / total_students)) * 100
            
            if percentile >= 90:
                return f'Top 10%', rank
            elif percentile >= 75:
                return f'Top 25%', rank
            elif percentile >= 50:
                return f'Top 50%', rank
            else:
                return f'Rank {rank}/{total_students}', rank
    
    return 'N/A', 0





@login_required
def student_dashboard(request, student_id):
    """
    Enhanced individual student dashboard with predictive analytics
    Supports both teacher and parent access with appropriate restrictions
    """
    student = get_object_or_404(Student, id=student_id)
    
    # # Check permission - UPDATED LOGIC
    # is_teacher = (student.student_class.teacher == request.user)
    # is_parent = hasattr(request.user, 'parent') and student.parent == request.user.parent

    
    # if not (is_teacher or is_parent):
    #     messages.error(request, "You don't have permission to view this dashboard.")
        
    #     # Redirect based on user type
    #     if request.user.user_type == 'parent':
    #         return redirect('authentication:parent_dashboard')  # Parents dashboard
    #     else:
    #         return redirect('students:student_list')  # Teachers list
    
    # Get all performance data
    # Use an unsliced queryset for calculations, and keep a sliced queryset for display
    attendance_qs = student.attendance_records.all().order_by('-date')
    attendance_records = attendance_qs[:30]
    academic_records = student.academic_records.all().order_by('-exam_date')
    non_academic_records = student.non_academic_records.all()
    
    # Calculate attendance percentage (use unsliced queryset for accurate filtering)
    total_days = attendance_qs.count()
    present_days = attendance_qs.filter(status='Present').count()
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Calculate monthly attendance trend
    monthly_attendance = []
    for i in range(6):
        month_start = datetime.now() - timedelta(days=30 * (i + 1))
        month_end = datetime.now() - timedelta(days=30 * i)
        month_records = student.attendance_records.filter(
            date__gte=month_start, 
            date__lte=month_end
        )
        total = month_records.count()
        present = month_records.filter(status='Present').count()
        percentage = (present / total * 100) if total > 0 else 0
        monthly_attendance.append({
            'month': month_start.strftime('%b'),
            'percentage': round(percentage, 1)
        })
    monthly_attendance.reverse()
    
    # Calculate academic average and subject-wise performance
    subject_performance = {}
    overall_scores = []
    
    for record in academic_records:
        subject_name = record.subject.name
        percentage = float(record.percentage)
        overall_scores.append(percentage)
        
        if subject_name not in subject_performance:
            subject_performance[subject_name] = {
                'scores': [],
                'exams': []
            }
        
        subject_performance[subject_name]['scores'].append(percentage)
        subject_performance[subject_name]['exams'].append({
            'name': record.exam_type.name,
            'score': percentage,
            'date': record.exam_date
        })
    
    # Calculate subject averages
    subject_averages = {
        subject: {
            'average': round(sum(data['scores']) / len(data['scores']), 1),
            'highest': round(max(data['scores']), 1),
            'lowest': round(min(data['scores']), 1),
            'exams': data['exams']
        }
        for subject, data in subject_performance.items()
    }
    
    # Calculate overall academic average
    academic_average = round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0
    
    # Get predictive analytics
    predictions = calculate_predictions(student)
    
    # Calculate class rank
    class_rank, rank_number = calculate_class_rank(student)
    
    # Calculate grade
    if academic_average >= 90:
        overall_grade = 'A+'
    elif academic_average >= 80:
        overall_grade = 'A'
    elif academic_average >= 70:
        overall_grade = 'B'
    elif academic_average >= 60:
        overall_grade = 'C'
    else:
        overall_grade = 'D'
    
    # Get performance trend (last 6 exams)
    recent_scores = overall_scores[-6:] if len(overall_scores) >= 6 else overall_scores
    if len(recent_scores) >= 2:
        trend_change = recent_scores[-1] - recent_scores[0]
        if trend_change > 5:
            trend_direction = 'up'
            trend_text = f'+{round(trend_change, 1)}%'
        elif trend_change < -5:
            trend_direction = 'down'
            trend_text = f'{round(trend_change, 1)}%'
        else:
            trend_direction = 'stable'
            trend_text = 'Stable'
    else:
        trend_direction = 'stable'
        trend_text = 'N/A'
    
    # Calculate attendance trend
    if len(monthly_attendance) >= 2:
        attendance_change = monthly_attendance[-1]['percentage'] - monthly_attendance[-2]['percentage']
        attendance_trend = f'+{round(attendance_change, 1)}%' if attendance_change > 0 else f'{round(attendance_change, 1)}%'
    else:
        attendance_trend = 'N/A'
    
    context = {
        'student': student,
        # 'is_teacher': is_teacher,
        # 'is_parent': is_parent,  # ← ADD THIS FLAG
        'attendance_percentage': round(attendance_percentage, 1),
        'attendance_trend': attendance_trend,
        'monthly_attendance': monthly_attendance,
        'academic_average': academic_average,
        'overall_grade': overall_grade,
        'class_rank': class_rank,
        'rank_number': rank_number,
        'subject_averages': subject_averages,
        'academic_records': academic_records[:10],  # Last 10 records
        'non_academic_records': non_academic_records,
        'predictions': predictions,
        'trend_direction': trend_direction,
        'trend_text': trend_text,
        'total_subjects': len(subject_averages),
        'total_exams': len(overall_scores),
    }

    print("Logged-in user:", request.user)
    print("Student:", student.first_name, student.last_name)
    print("Student's Parent:", student.parent)
    print("Is Parent Match:", student.parent == request.user)
    print("Is Teacher Match:", student.student_class.teacher == request.user)
    
    
    return render(request, 'students/student_dashboard.html', context)


@login_required
def get_student_chart_data(request, student_id):
    """
    API endpoint for dynamic chart data with enhanced analytics
    Supports both teacher and parent access
    """
    student = get_object_or_404(Student, id=student_id)
    
    # ============= UPDATED ACCESS CONTROL =============
    # Check permission
    if not (student.student_class.teacher == request.user or student.parent == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    # ============= END ACCESS CONTROL =============
    
    chart_type = request.GET.get('type', 'performance_trend')
    
    # ... rest of your existing chart code remains exactly the same ...
    
    if chart_type == 'performance_trend':
        # Get performance over time
        records = student.academic_records.all().order_by('exam_date')
        
        # Group by month
        monthly_data = {}
        for record in records:
            month_key = record.exam_date.strftime('%b %Y')
            if month_key not in monthly_data:
                monthly_data[month_key] = []
            monthly_data[month_key].append(float(record.percentage))
        
        # Calculate averages
        labels = list(monthly_data.keys())
        student_values = [sum(scores) / len(scores) for scores in monthly_data.values()]
        
        # Calculate class average for comparison
        class_averages = []
        for month in labels:
            # Get all students in class for this month
            class_avg = AcademicPerformance.objects.filter(
                student__student_class=student.student_class
            ).aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
            class_averages.append(round(float(class_avg) * 100 / 100, 1))
        
        data = {
            'labels': labels,
            'student_values': [round(v, 1) for v in student_values],
            'class_averages': class_averages
        }
    
    elif chart_type == 'subject_scores':
        # Get average score per subject
        records = student.academic_records.all()
        subject_data = {}
        
        for record in records:
            subject = record.subject.name
            if subject not in subject_data:
                subject_data[subject] = []
            subject_data[subject].append(float(record.percentage))
        
        data = {
            'labels': list(subject_data.keys()),
            'values': [round(sum(scores) / len(scores), 1) for scores in subject_data.values()]
        }
    
    elif chart_type == 'attendance_pattern':
        # Weekly attendance for last 4 weeks
        weekly_data = []
        for i in range(4):
            week_start = datetime.now() - timedelta(days=7 * (i + 1))
            week_end = datetime.now() - timedelta(days=7 * i)
            week_records = student.attendance_records.filter(
                date__gte=week_start,
                date__lte=week_end
            )
            present = week_records.filter(status='Present').count()
            absent = week_records.filter(status='Absent').count()
            weekly_data.append({'present': present, 'absent': absent})
        
        weekly_data.reverse()
        
        data = {
            'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'present': [w['present'] for w in weekly_data],
            'absent': [w['absent'] for w in weekly_data]
        }
    
    elif chart_type == 'skills_radar':
        # Non-academic skills
        latest_record = student.non_academic_records.first()
        if latest_record:
            data = {
                'labels': ['Leadership', 'Teamwork', 'Communication', 'Punctuality', 'Discipline'],
                'values': [
                    latest_record.leadership_skills,
                    latest_record.teamwork,
                    latest_record.communication_skills,
                    latest_record.punctuality,
                    8 if latest_record.discipline == 'Excellent' else 6 if latest_record.discipline == 'Good' else 4
                ]
            }
        else:
            data = {'labels': [], 'values': []}
    
    elif chart_type == 'comparative':
        # Student vs class average by subject
        records = student.academic_records.all()
        subject_scores = {}
        
        for record in records:
            subject = record.subject.name
            if subject not in subject_scores:
                subject_scores[subject] = []
            subject_scores[subject].append(float(record.percentage))
        
        student_averages = {
            subject: sum(scores) / len(scores)
            for subject, scores in subject_scores.items()
        }
        
        # Get class averages
        class_averages = {}
        for subject in subject_scores.keys():
            avg = AcademicPerformance.objects.filter(
                student__student_class=student.student_class,
                subject__name=subject
            ).aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
            class_averages[subject] = round(float(avg), 1)
        
        data = {
            'labels': list(student_averages.keys()),
            'student_values': [round(v, 1) for v in student_averages.values()],
            'class_values': list(class_averages.values())
        }
    
    elif chart_type == 'growth_timeline':
        # Performance across all exams chronologically
        records = student.academic_records.all().order_by('exam_date')
        
        labels = []
        values = []
        
        for record in records[:10]:  # Last 10 exams
            labels.append(f"{record.exam_type.name[:8]}")
            values.append(round(float(record.percentage), 1))
        
        data = {
            'labels': labels,
            'values': values
        }
    
    else:
        return JsonResponse({'error': 'Invalid chart type'}, status=400)
    
    return JsonResponse(data)



@login_required
def get_class_statistics(request, class_id):
    """
    API endpoint for class-level statistics
    """
    class_obj = get_object_or_404(Class, id=class_id)
    
    # Check permission - must be the class teacher
    if class_obj.teacher != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    students = class_obj.students.all()
    
    # Calculate class-wide metrics
    total_students = students.count()
    
    # Attendance statistics
    attendance_stats = Attendance.objects.filter(
        student__in=students
    ).aggregate(
        total_days=Count('id'),
        present_days=Count('id', filter=Q(status='Present')),
        absent_days=Count('id', filter=Q(status='Absent'))
    )
    
    class_attendance_rate = 0
    if attendance_stats['total_days'] > 0:
        class_attendance_rate = (attendance_stats['present_days'] / attendance_stats['total_days']) * 100
    
    # Academic statistics
    academic_stats = AcademicPerformance.objects.filter(
        student__in=students
    ).aggregate(
        avg_score=Avg('marks_obtained'),
        highest_score=Max('marks_obtained'),
        lowest_score=Min('marks_obtained'),
        total_exams=Count('id')
    )
    
    # Top performers (top 5)
    student_averages = []
    for student in students:
        avg = student.academic_records.aggregate(Avg('marks_obtained'))['marks_obtained__avg']
        if avg:
            student_averages.append({
                'student_id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'roll_number': student.roll_number,
                'average': round(float(avg), 1)
            })
    
    student_averages.sort(key=lambda x: x['average'], reverse=True)
    top_performers = student_averages[:5]
    
    # Subject-wise class average
    subjects_performance = {}
    for student in students:
        for record in student.academic_records.all():
            subject_name = record.subject.name
            if subject_name not in subjects_performance:
                subjects_performance[subject_name] = []
            subjects_performance[subject_name].append(float(record.percentage))
    
    subject_averages = {
        subject: round(sum(scores) / len(scores), 1)
        for subject, scores in subjects_performance.items()
    }
    
    return JsonResponse({
        'total_students': total_students,
        'attendance': {
            'rate': round(class_attendance_rate, 1),
            'total_days': attendance_stats['total_days'],
            'present_days': attendance_stats['present_days'],
            'absent_days': attendance_stats['absent_days']
        },
        'academics': {
            'average': round(float(academic_stats['avg_score'] or 0), 1),
            'highest': round(float(academic_stats['highest_score'] or 0), 1),
            'lowest': round(float(academic_stats['lowest_score'] or 0), 1),
            'total_exams': academic_stats['total_exams']
        },
        'top_performers': top_performers,
        'subject_averages': subject_averages
    })

@login_required
def get_performance_summary(request, student_id):
    """
    API endpoint for complete performance summary
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Check permission
    if not (student.student_class.teacher == request.user or student.parent == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
       
    # Get all data
    academic_records = student.academic_records.all()
    attendance_records = student.attendance_records.all()
    
    # Calculate metrics
    total_exams = academic_records.count()
    avg_score = academic_records.aggregate(Avg('marks_obtained'))['marks_obtained__avg'] or 0
    
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='Present').count()
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Subject breakdown
    subjects = {}
    for record in academic_records:
        subject_name = record.subject.name
        if subject_name not in subjects:
            subjects[subject_name] = []
        subjects[subject_name].append(float(record.percentage))
    
    subject_summary = {
        name: {
            'average': round(sum(scores) / len(scores), 1),
            'highest': round(max(scores), 1),
            'lowest': round(min(scores), 1),
            'total_exams': len(scores)
        }
        for name, scores in subjects.items()
    }
    
    return JsonResponse({
        'total_exams': total_exams,
        'average_score': round(float(avg_score), 1),
        'attendance_rate': round(attendance_rate, 1),
        'subjects': subject_summary,
        'strongest_subject': max(subject_summary, key=lambda x: subject_summary[x]['average']) if subject_summary else 'N/A',
        'weakest_subject': min(subject_summary, key=lambda x: subject_summary[x]['average']) if subject_summary else 'N/A'
    })


@login_required
def get_predictions(request, student_id):
    """
    API endpoint for prediction data only
    """
    student = get_object_or_404(Student, id=student_id)
    
    # Check permission (updated for parents)
    # Check permission
    if not (student.student_class.teacher == request.user or student.parent == request.user):
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    predictions = calculate_predictions(student)
    class_rank, rank_number = calculate_class_rank(student)
    
    return JsonResponse({
        'predictions': predictions,
        'class_rank': class_rank,
        'rank_number': rank_number
    })