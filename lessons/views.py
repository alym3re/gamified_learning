
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Lesson, LessonCategory, LessonProgress
from .forms import LessonForm, LessonCategoryForm
from dashboard.models import ActivityLog
from django.utils import timezone

def lesson_list(request):
    categories = LessonCategory.objects.all()
    category_id = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search_query = request.GET.get('q')
    
    lessons = Lesson.objects.filter(is_active=True)
    
    if category_id:
        lessons = lessons.filter(category__id=category_id)
    
    if difficulty:
        lessons = lessons.filter(difficulty=difficulty)
    
    if search_query:
        lessons = lessons.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(lessons.order_by('-upload_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'selected_difficulty': difficulty,
        'search_query': search_query or ''
    }
    return render(request, 'lessons/list.html', context)

@login_required
def view_lesson(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug, is_active=True)
    
    # Track lesson view
    lesson.increment_view_count()
    
    # Record activity
    ActivityLog.objects.create(
        user=request.user,
        activity_type='lesson',
        object_id=lesson.id,
        xp_earned=10
    )
    
    # Update or create progress
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.last_viewed = timezone.now()
    progress.save()
    
    # Check if file can be previewed
    can_preview = lesson.extension() in ['.pdf', '.txt', '.md']
    
    # --- New: Compute related lessons safely for the template ---
    if lesson.category:
        related_lessons = (lesson.category.lesson_set
                           .exclude(id=lesson.id)
                           .order_by('-upload_date')[:5])
    else:
        related_lessons = []

    context = {
        'lesson': lesson,
        'can_preview': can_preview,
        'progress': progress,
        'related_lessons': related_lessons,
    }
    return render(request, 'lessons/view.html', context)

@login_required
def upload_lesson(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to upload lessons.")
        return redirect('lessons:lesson_list')
    
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
def manage_categories(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to manage categories.")
        return redirect('lessons:lesson_list')
    
    if request.method == 'POST':
        form = LessonCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('lessons:manage_categories')
    else:
        form = LessonCategoryForm()
    
    categories = LessonCategory.objects.all()
    return render(request, 'lessons/categories.html', {
        'form': form,
        'categories': categories
    })

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
