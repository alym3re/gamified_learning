from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from lessons.models import Lesson
from quizzes.models import QuizAttempt, Quiz
from exams.models import Exam
from exams.models import ExamAttempt
from .models import StudentProgress, ActivityLog, Badge
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard(request):
    if request.user.is_staff:
        return admin_dashboard(request)
    return student_dashboard(request)

@login_required
def student_dashboard(request):
    # Get or create student progress
    progress, created = StudentProgress.objects.get_or_create(user=request.user)
    
    # Recent activities
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]
    
    # Recent lessons (last 5 viewed)
    recent_lessons = Lesson.objects.filter(
        id__in=ActivityLog.objects.filter(
            user=request.user,
            activity_type='lesson'
        ).values_list('object_id', flat=True)
    ).distinct()[:5]
    
    # Quiz and exam attempts
    quiz_attempts = QuizAttempt.objects.filter(user=request.user, completed=True).order_by('-end_time')[:5]
    exam_attempts = ExamAttempt.objects.filter(user=request.user, completed=True).order_by('-end_time')[:5]
    
    # Calculate progress stats
    total_lessons = Lesson.objects.count()
    completed_lessons = ActivityLog.objects.filter(
        user=request.user,
        activity_type='lesson'
    ).values('object_id').distinct().count()
    
    lesson_progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    context = {
        'progress': progress,
        'activities': activities,
        'recent_lessons': recent_lessons,
        'quiz_attempts': quiz_attempts,
        'exam_attempts': exam_attempts,
        'lesson_progress': round(lesson_progress, 1),
        'badges': progress.badges.all()[:4],
    }
    return render(request, 'dashboard/student.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('student_dashboard')
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # User statistics
    total_users = User.objects.count()
    new_users_week = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=7)
    ).count()
    active_users = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Content statistics
    total_lessons = Lesson.objects.count()
    total_quizzes = Quiz.objects.count()
    total_exams = Exam.objects.count()
    
    # Activity statistics
    recent_activities = ActivityLog.objects.all().order_by('-timestamp')[:10]
    quiz_stats = QuizAttempt.objects.filter(completed=True).aggregate(
        avg_score=Avg('score'),
        high_score=Max('score')
    )
    exam_stats = ExamAttempt.objects.filter(completed=True).aggregate(
        avg_score=Avg('score'),
        pass_rate=Avg('passed')
    )
    
    context = {
        'total_users': total_users,
        'new_users_week': new_users_week,
        'active_users': active_users,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'total_exams': total_exams,
        'recent_activities': recent_activities,
        'quiz_stats': quiz_stats,
        'exam_stats': exam_stats,
    }
    return render(request, 'dashboard/admin.html', context)