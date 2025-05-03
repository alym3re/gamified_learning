import random
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.views.decorators.http import require_POST
from .models import Quiz, Question, Answer, QuizAttempt, UserAnswer, GRADING_PERIOD_CHOICES, QUESTION_TYPE_CHOICES, LockedQuizPeriod
from .forms import QuizForm, QuestionForm, AnswerForm, AnswerFormSet, MultipleChoiceFormSet

def grading_period_list(request):
    periods = GRADING_PERIOD_CHOICES
    period_stats = {}
    user = request.user if request.user.is_authenticated else None
    
    # Load locks
    locked_periods = {lk.period: lk.locked for lk in LockedQuizPeriod.objects.all()}

    for period_value, period_label in periods:
        quizzes = Quiz.objects.filter(grading_period=period_value, is_active=True, is_archived=False)
        quiz_count = quizzes.count()
        view_count = quizzes.aggregate(total_views=models.Sum("view_count"))["total_views"] or 0

        # Progress: How many quizzes in this period has the user completed?
        progress_percent = 0
        user_completed = 0
        if user:
            done_ids = QuizAttempt.objects.filter(
                user=user, quiz__grading_period=period_value, completed=True
            ).values_list("quiz_id", flat=True)
            user_completed = quizzes.filter(id__in=done_ids).count()
            progress_percent = (user_completed / quiz_count) * 100 if quiz_count > 0 else 0
        
        locked = locked_periods.get(period_value, False)

        quizzes_for_period = list(quizzes.order_by('-created_at'))

        period_stats[period_value] = {
            "label": period_label,
            "quiz_count": quiz_count,
            "view_count": view_count,
            "progress_percent": progress_percent,
            "completed_count": user_completed,
            "quizzes": quizzes_for_period,
            "locked": locked,
        }

    context = {
        "periods": periods,
        "period_stats": period_stats,
        "is_admin": user.is_staff if user else False,
    }
    return render(request, "quizzes/grading_period_list.html", context)

def quiz_list_by_period(request, grading_period):
    valid_periods = [c[0] for c in GRADING_PERIOD_CHOICES]
    if grading_period not in valid_periods:
        from django.contrib import messages
        messages.error(request, "Invalid grading period.")
        return redirect('quizzes:grading_period_list')

    quizzes_qs = Quiz.objects.filter(is_active=True, grading_period=grading_period).order_by('-created_at')
    period_display = dict(GRADING_PERIOD_CHOICES)[grading_period]
    paginator = Paginator(quizzes_qs, 12)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    completed_quiz_ids = set()
    if request.user.is_authenticated:
        completed_quiz_ids = set(
            QuizAttempt.objects.filter(
                user=request.user, quiz__grading_period=grading_period, completed=True
            ).values_list('quiz_id', flat=True)
        )
    
    context = {
        'grading_period': grading_period,
        'grading_period_display': period_display,
        'page_obj': page_obj,
        'user': request.user,
        'completed_quiz_ids': completed_quiz_ids,  # let template display "Completed"
    }
    return render(request, "quizzes/list.html", context)


@login_required
def quiz_list(request):
    return redirect('quizzes:grading_period_list')

@login_required
def view_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True, is_archived=False)
    if hasattr(quiz, 'increment_view_count'):
        quiz.increment_view_count()
    questions = quiz.questions.all().prefetch_related('answers')
    
    # Check if current user has completed this quiz
    completed = False
    attempt = None
    if request.user.is_authenticated:
        attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
        completed = attempt.completed if attempt else False
    
    # Leaderboard: all completed attempts, ordered highest score, shortest duration, latest first
    leaderboard_attempts = (
        QuizAttempt.objects
        .filter(quiz=quiz, completed=True)
        .select_related('user')
        .order_by('-score', 'end_time', 'start_time')
    )

    # Pagination for leaderboard (10 per page)
    page = request.GET.get('leaderboard_page', 1)
    leaderboard_paginator = Paginator(leaderboard_attempts, 10)
    try:
        leaderboard_page_obj = leaderboard_paginator.page(page)
    except PageNotAnInteger:
        leaderboard_page_obj = leaderboard_paginator.page(1)
    except EmptyPage:
        leaderboard_page_obj = leaderboard_paginator.page(leaderboard_paginator.num_pages)
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'leaderboard_page_obj': leaderboard_page_obj,
        'completed': completed,  # For template logic to block attempt or show DONE
        'user_attempt': attempt,
    }
    
    if quiz.locked and not request.user.is_staff:
        messages.error(request, "This quiz is locked.")
        return redirect('quizzes:grading_period_list')
    return render(request, "quizzes/view.html", context)

@login_required
def create_quiz(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create quizzes.")
        return redirect('quizzes:grading_period_list')
    
    if request.method == 'POST':
        form = QuizForm(request.POST, request.FILES)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect('quizzes:add_quiz_questions', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'quizzes/create.html', {'form': form})

@login_required
def upload_quiz(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to upload quizzes.")
        return redirect('quizzes:grading_period_list')
    if request.method == 'POST':
        form = QuizForm(request.POST, request.FILES)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz uploaded successfully!')
            return redirect('quizzes:view_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'quizzes/upload.html', {'form': form})

@login_required
def add_quiz_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not request.user.is_staff or quiz.created_by != request.user:
        messages.error(request, "You don't have permission to edit this quiz.")
        return redirect('quizzes:quiz_list_by_period', grading_period=quiz.grading_period)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST, prefix='answers')
        if question_form.is_valid():
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.save()
                
                question_type = question.question_type
                
                if question_type.startswith('multiple') or question_type == 'true_false':
                    answer_formset = AnswerFormSet(request.POST, prefix='answers', instance=question)
                    if answer_formset.is_valid():
                        answers = answer_formset.save(commit=False)
                        for answer in answers:
                            answer.question = question
                            answer.save()
                    
                        # Check if at least one correct answer exists
                        if not any(answer.is_correct for answer in answers):
                            messages.error(request, "At least one answer must be marked as correct.")
                            return render(request, 'quizzes/add_questions.html', {
                                'quiz': quiz,
                                'question_form': question_form,
                                'answer_formset': answer_formset,
                                'questions': quiz.questions.all().prefetch_related('answers'),
                                'error': "At least one answer must be marked as correct.",
                            })
                    else:
                        return render(request, 'quizzes/add_questions.html', {
                            'quiz': quiz,
                            'question_form': question_form,
                            'answer_formset': answer_formset,
                            'questions': quiz.questions.all().prefetch_related('answers'),
                            'error': "Error in answers",
                        })
                elif question_type == 'identification':
                    answer = Answer.objects.create(
                        question=question,
                        text=request.POST.get('correct_answer', '').strip(),
                        is_correct=True
                    )
                
                messages.success(request, 'Question added successfully!')
                return redirect('quizzes:add_quiz_questions', quiz_id=quiz.id)
        else:
            return render(request, 'quizzes/add_questions.html', {
                'quiz': quiz,
                'question_form': question_form,
                'answer_formset': answer_formset,
                'questions': quiz.questions.all().prefetch_related('answers'),
                'error': "Invalid question form",
            })
    else:
        question_form = QuestionForm()
        answer_formset = AnswerFormSet(prefix='answers')
    
    questions = quiz.questions.all().prefetch_related('answers')
    return render(request, 'quizzes/add_questions.html', {
        'quiz': quiz,
        'question_form': question_form,
        'answer_formset': answer_formset,
        'questions': questions
    })

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True, is_archived=False)
    
    # Restrict to ONE complete attempt per user
    # If attempt exists for user & quiz, block further access.
    user_attempt = QuizAttempt.objects.filter(user=request.user, quiz=quiz).first()
    if user_attempt and user_attempt.completed:
        messages.info(request, "You have already completed this quiz. You cannot take it again.")
        return redirect('quizzes:view_quiz', quiz_id=quiz.id)
    elif user_attempt is None:
        user_attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
    
    if quiz.locked and not request.user.is_staff:
        messages.error(request, "This quiz is locked.")
        return redirect('quizzes:grading_period_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            total_points = 0
            total_score = 0
            
            for question in quiz.questions.all():
                question_type = question.question_type
                user_answer_obj, _ = UserAnswer.objects.get_or_create(attempt=user_attempt, question=question)
                user_answer_obj.is_correct = False
                
                if question_type.startswith('multiple'):
                    choice_ids = request.POST.getlist(f'question_{question.id}')
                    # Limit to one answer for single choice questions
                    if question_type == 'multiple_single' and len(choice_ids) > 1:
                        choice_ids = choice_ids[:1]
                    
                    selected_answers = Answer.objects.filter(question=question, id__in=choice_ids)
                    user_answer_obj.selected_answers.set(selected_answers)
                    user_answer_obj.text_answer = None  # Clear text field for MCQ
                
                elif question_type == 'true_false':
                    answer_val = request.POST.get(f'question_{question.id}')
                    user_answer_obj.selected_answers.clear()
                    user_answer_obj.text_answer = None
                    
                    if answer_val and answer_val.isdigit():
                        selected_answer = Answer.objects.filter(pk=answer_val, question=question).first()
                        if selected_answer:
                            user_answer_obj.selected_answers.add(selected_answer)
                    elif answer_val:
                        user_answer_obj.text_answer = answer_val
                
                elif question_type == 'identification':
                    answer_text = request.POST.get(f'question_{question.id}', '').strip()
                    user_answer_obj.text_answer = answer_text
                    user_answer_obj.selected_answers.clear()
                
                user_answer_obj.save()
                user_answer_obj.check_answer()  # Call the model method to check if answer is correct
                
                if user_answer_obj.is_correct:
                    total_score += question.points
                total_points += question.points
            
            user_attempt.completed = True
            user_attempt.end_time = timezone.now()
            user_attempt.score = (total_score / total_points) * 100 if total_points > 0 else 0
            user_attempt.passed = user_attempt.score >= quiz.passing_score
            user_attempt.save()
            
            messages.success(request, 'Quiz submitted successfully!')
            return redirect('quizzes:quiz_results', attempt_id=user_attempt.id)
    
    questions = quiz.questions.all().prefetch_related('answers')
    if quiz.shuffle_questions:
        questions = list(questions)
        random.shuffle(questions)
    
    return render(request, 'quizzes/take.html', {
        'quiz': quiz,
        'attempt': user_attempt,
        'questions': questions,
        'time_limit': quiz.time_limit * 60 if quiz.time_limit > 0 else None
    })

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    if not attempt.completed:
        messages.error(request, "This quiz attempt is not completed yet.")
        return redirect('quizzes:grading_period_list')

    # Select related so we can access user_answer.question easily in template
    user_answers = attempt.user_answers.select_related('question').all()

    return render(request, 'quizzes/results.html', {
        'attempt': attempt,
        'user_answers': user_answers,
        'show_answers': attempt.quiz.show_correct_answers or attempt.passed or request.user.is_staff
    })


@login_required
def quiz_history(request):
    attempts = QuizAttempt.objects.filter(
        user=request.user,
        completed=True
    ).select_related('quiz').order_by('-start_time')

    grading_period = request.GET.get('grading_period')
    if grading_period:
        attempts = attempts.filter(quiz__grading_period=grading_period)
    paginator = Paginator(attempts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'quizzes/history.html', {'page_obj': page_obj})

@login_required
def delete_question(request, quiz_id, question_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not request.user.is_staff or quiz.created_by != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    question.delete()
    return JsonResponse({'success': True})

@login_required
@user_passes_test(lambda u: u.is_staff)
def archive_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    quiz.is_archived = True
    quiz.save(update_fields=['is_archived'])
    messages.success(request, f'Quiz "{quiz.title}" archived.')
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('quizzes:view_quiz', quiz_id=quiz.id)

@login_required
@user_passes_test(lambda u: u.is_staff)
def unarchive_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    quiz.is_archived = False
    quiz.save(update_fields=['is_archived'])
    messages.success(request, f'Quiz "{quiz.title}" unarchived.')
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('quizzes:view_quiz', quiz_id=quiz.id)
    
@require_POST
@login_required
@user_passes_test(lambda u: u.is_staff)
def toggle_period_lock(request, period_value):
    """Allows staff to toggle lock/unlock of a grading period."""
    valid_periods = [c[0] for c in GRADING_PERIOD_CHOICES]
    if period_value not in valid_periods:
        messages.error(request, "Invalid grading period.")
        return redirect('quizzes:grading_period_list')
        
    lock, created = LockedQuizPeriod.objects.get_or_create(period=period_value)
    lock.locked = not lock.locked
    lock.save()
    
    action = "locked" if lock.locked else "unlocked"
    period_display = dict(GRADING_PERIOD_CHOICES)[period_value]
    messages.success(request, f"Period '{period_display}' has been {action}.")
    
    return redirect('quizzes:grading_period_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def lock_quiz(request, quiz_id):
    """Allows staff to lock a specific quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.locked = True
    quiz.save(update_fields=["locked"])
    messages.success(request, f"Quiz '{quiz.title}' has been locked.")
    return redirect(request.META.get("HTTP_REFERER", "quizzes:grading_period_list"))

@login_required
@user_passes_test(lambda u: u.is_staff)
def unlock_quiz(request, quiz_id):
    """Allows staff to unlock a specific quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    quiz.locked = False
    quiz.save(update_fields=["locked"])
    messages.success(request, f"Quiz '{quiz.title}' has been unlocked.")
    return redirect(request.META.get("HTTP_REFERER", "quizzes:grading_period_list"))

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.created_by != request.user:
        messages.error(request, "You don't have permission to edit this quiz.")
        return redirect('quizzes:quiz_list_by_period', grading_period=quiz.grading_period)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, request.FILES, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect('quizzes:view_quiz', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'quizzes/edit.html', {
        'form': form,
        'quiz': quiz
    })
