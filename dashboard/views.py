from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from lessons.models import Lesson
from quizzes.models import QuizAttempt
from django.contrib.auth import get_user_model

@login_required
def student_dashboard(request):
    recent_lessons = Lesson.objects.filter(is_active=True).order_by('-upload_date')[:5]
    quiz_attempts = QuizAttempt.objects.filter(user=request.user, completed=True).order_by('-end_time')[:5]
    
    context = {
        'recent_lessons': recent_lessons,
        'quiz_attempts': quiz_attempts,
        'user': request.user
    }
    return render(request, 'dashboard/student.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('student_dashboard')
    
    User = get_user_model()
    total_users = User.objects.count()
    total_lessons = Lesson.objects.count()
    total_quizzes = Quiz.objects.count()
    
    context = {
        'total_users': total_users,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes
    }
    return render(request, 'dashboard/admin.html', context)