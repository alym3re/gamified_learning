from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from .models import Lesson, LessonProgress, LessonAccess, GRADING_PERIOD_CHOICES
from .forms import LessonForm
from django.utils import timezone

def grading_period_list(request):
    periods = GRADING_PERIOD_CHOICES
    context = {
        "periods": periods,
    }
    return render(request, 'lessons/grading_period_list.html', context)

def lesson_list_by_period(request, grading_period):
    # validate grading_period
    valid_periods = [c[0] for c in GRADING_PERIOD_CHOICES]
    if grading_period not in valid_periods:
        messages.error(request, "Invalid grading period.")
        return redirect('lessons:grading_period_list')
    lessons = Lesson.objects.filter(is_active=True, grading_period=grading_period).order_by('-upload_date')
    period_display = dict(GRADING_PERIOD_CHOICES)[grading_period]
    paginator = Paginator(lessons, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'grading_period': grading_period,
        'grading_period_display': period_display,
        'page_obj': page_obj,
    }
    return render(request, "lessons/list.html", context)

@login_required
def view_lesson(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_active=True)
    # Track lesson view
    LessonAccess.objects.create(user=request.user, lesson=lesson, access_type='view')
    lesson.increment_view_count()
    # Progress handling
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.last_viewed = timezone.now()
    progress.save()
    # Admin can see who viewed and downloaded
    lesson_access = None
    if request.user.is_staff:
        lesson_access = LessonAccess.objects.filter(lesson=lesson).order_by('-timestamp')
    # For templates, get display value for grading period
    grading_period_display = dict(GRADING_PERIOD_CHOICES).get(lesson.grading_period, lesson.grading_period)
    context = {
        'lesson': lesson,
        'progress': progress,
        'lesson_access': lesson_access,
        'grading_period_display': grading_period_display,
    }
    return render(request, "lessons/view.html", context)

@login_required
def upload_lesson(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to upload lessons.")
        return redirect('lessons:grading_period_list')
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.uploaded_by = request.user
            lesson.save()
            messages.success(request, 'Lesson uploaded successfully!')
            return redirect('lessons:view_lesson', slug=lesson.slug)
    else:
        form = LessonForm()
    return render(request, 'lessons/upload.html', {'form': form})

@login_required
def mark_completed(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.completed = not progress.completed
    progress.save()
    action = "completed" if progress.completed else "marked incomplete"
    messages.success(request, f'Lesson {action} successfully!')
    return redirect('lessons:view_lesson', slug=slug)

@login_required
def download_lesson_file(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_active=True)
    LessonAccess.objects.create(user=request.user, lesson=lesson, access_type='download')
    file_handle = lesson.file
    if not file_handle:
        raise Http404("File not found.")
    response = HttpResponse(file_handle, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_handle.name.split('/')[-1]}"'
    return response

@user_passes_test(lambda u: u.is_staff)
def admin_lesson_access_report(request):
    access_logs = LessonAccess.objects.select_related('lesson', 'user').order_by('-timestamp')
    context = {
        "access_logs": access_logs
    }
    return render(request, "lessons/access_report.html", context)