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
from .models import Exam, ExamQuestion, ExamAnswer, ExamAttempt, ExamUserAnswer, EXAM_GRADING_PERIOD_CHOICES, EXAM_QUESTION_TYPE_CHOICES
from .forms import ExamForm, ExamQuestionForm, ExamAnswerForm, ExamAnswerFormSet, ExamMultipleChoiceFormSet, ExamTrueFalseFormSet, ExamFillInTheBlanksForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required




def grading_period_exam_list(request):
    periods = EXAM_GRADING_PERIOD_CHOICES
    period_stats = {}
    user = request.user if request.user.is_authenticated else None

    for period_value, period_label in periods:
        try:
            exam = Exam.objects.get(grading_period=period_value)
            exam_count = 1
            view_count = exam.view_count
            questions_count = exam.question_count()
            completed = False
            exam_attempt = None
            if user:
                exam_attempt = ExamAttempt.objects.filter(user=user, exam=exam, completed=True).first()
                completed = bool(exam_attempt)
            exams_for_period = [exam]
        except Exam.DoesNotExist:
            exam = None
            exam_count = 0
            view_count = 0
            questions_count = 0
            completed = False
            exams_for_period = []

        period_stats[period_value] = {
            "label": period_label,
            "exam_count": exam_count,
            "view_count": view_count,
            "questions_count": questions_count,
            "completed": completed,
            "exams": exams_for_period,
            "exam": exam,
        }

    context = {
        "periods": periods,
        "period_stats": period_stats,
        "is_admin": user.is_staff if user else False,
    }
    return render(request, "exams/grading_period_exam_list.html", context)

@login_required
def create_exam(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create exams.")
        return redirect('exams:grading_period_exam_list')

    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                exam = form.save(commit=False)
                exam.created_by = request.user
                exam.save()
                messages.success(request, 'Exam created successfully!')
                return redirect('exams:add_exam_questions', exam_id=exam.id)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = ExamForm()

    return render(request, 'exams/create.html', {'form': form})

def exam_by_period(request, grading_period):
    valid_periods = [c[0] for c in EXAM_GRADING_PERIOD_CHOICES]
    if grading_period not in valid_periods:
        messages.error(request, "Invalid grading period.")
        return redirect('exams:grading_period_exam_list')

    try:
        exam = Exam.objects.get(grading_period=grading_period)
    except Exam.DoesNotExist:
        exam = None

    context = {
        'grading_period': grading_period,
        'grading_period_display': dict(EXAM_GRADING_PERIOD_CHOICES)[grading_period],
        'exam': exam,
        'user': request.user,
    }
    return render(request, "exams/by_period.html", context)

@login_required
def exam_list(request):
    return redirect('exams:grading_period_exam_list')

@login_required
def view_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if hasattr(exam, 'increment_view_count'):
        exam.increment_view_count()
    questions = exam.get_ordered_questions()
    
    completed = False
    attempt = None
    if request.user.is_authenticated:
        attempt = ExamAttempt.objects.filter(user=request.user, exam=exam).first()
        completed = attempt.completed if attempt else False
    
    context = {
        'exam': exam,
        'questions': questions,
        'completed': completed,
        'user_attempt': attempt,
    }
    if exam.locked and not request.user.is_staff:
        messages.error(request, "This exam is locked.")
        return redirect('exams:grading_period_exam_list')
    return render(request, "exams/view.html", context)

def get_answer_formset_for_question_type(question_type):
    """Return the appropriate formset based on question type"""
    if question_type == 'multiple_choice':
        return ExamMultipleChoiceFormSet
    elif question_type == 'true_false':
        return ExamTrueFalseFormSet
    else:
        return ExamAnswerFormSet

@login_required
def add_exam_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff or exam.created_by != request.user:
        messages.error(request, "You don't have permission to edit this exam.")
        return redirect('exams:exam_by_period', grading_period=exam.grading_period)

    default_question_type = 'multiple_choice'
    error_message = None

    if request.method == 'POST':
        qtype = request.POST.get('question_type', default_question_type)
        if qtype == 'fill_in_the_blanks':
            question_form = ExamFillInTheBlanksForm(request.POST)
            answer_formset = None
        else:
            question_form = ExamQuestionForm(request.POST)
            AnswerFormSet = get_answer_formset_for_question_type(qtype)
            answer_formset = AnswerFormSet(request.POST, prefix='answers') if AnswerFormSet else None

        if question_form.is_valid() and (answer_formset is None or answer_formset.is_valid()):
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.exam = exam
                question.save()

                if qtype == 'fill_in_the_blanks':
                    # Save each blank as an ExamAnswer
                    answers_list = question_form.cleaned_data['answers_list']
                    for blank_answer in answers_list:
                        ExamAnswer.objects.create(
                            question=question,
                            text=blank_answer.strip(),
                            is_correct=True
                        )
                elif qtype == 'true_false':
                    # Ensure exactly two ExamAnswer options: True and False
                    if answer_formset is not None:
                        answers = answer_formset.save(commit=False)
                        # Delete any existing answers first
                        ExamAnswer.objects.filter(question=question).delete()
                        # Create True and False options
                        for idx, answer in enumerate(answers):
                            answer.question = question
                            answer.text = 'True' if idx == 0 else 'False'
                            answer.save()
                else:
                    # For multiple choice and other types
                    if answer_formset is not None:
                        answers = answer_formset.save(commit=False)
                        for answer in answers:
                            answer.question = question
                            answer.save()
                        answer_formset.save_m2m()
                        
                messages.success(request, 'Question added successfully!')
                return redirect('exams:add_exam_questions', exam_id=exam.id)
        else:
            error_message = "Invalid question or answer form"
    else:
        qtype = request.GET.get('question_type', default_question_type)
        if qtype == 'fill_in_the_blanks':
            question_form = ExamFillInTheBlanksForm(initial={'question_type': 'fill_in_the_blanks'})
            answer_formset = None
        else:
            question_form = ExamQuestionForm(initial={'question_type': qtype})
            AnswerFormSet = get_answer_formset_for_question_type(qtype)
            
            if qtype == 'true_false' and AnswerFormSet:
                # Pre-fill with "True" and "False"
                answer_formset = AnswerFormSet(
                    prefix='answers',
                    initial=[
                        {'text': 'True', 'is_correct': False},
                        {'text': 'False', 'is_correct': False}
                    ]
                )
            else:
                answer_formset = AnswerFormSet(prefix='answers') if AnswerFormSet else None

    questions = exam.get_ordered_questions()
    return render(request, 'exams/add_questions.html', {
        'exam': exam,
        'question_form': question_form,
        'answer_formset': answer_formset,
        'questions': questions,
        'error': error_message,
    })


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    user_attempt = ExamAttempt.objects.filter(user=request.user, exam=exam).first()
    if user_attempt and user_attempt.completed:
        messages.info(request, "You have already completed this exam. You cannot take it again.")
        return redirect('exams:view_exam', exam_id=exam.id)
    elif user_attempt is None:
        user_attempt = ExamAttempt.objects.create(user=request.user, exam=exam)

    if exam.locked and not request.user.is_staff:
        messages.error(request, "This exam is locked.")
        return redirect('exams:grading_period_exam_list')

    if request.method == 'POST':
        with transaction.atomic():
            total_points = 0
            total_score = 0

            for question in exam.get_ordered_questions():
                question_type = question.question_type
                user_answer_obj, _ = ExamUserAnswer.objects.get_or_create(attempt=user_attempt, question=question)
                user_answer_obj.is_correct = False

                if question_type.startswith('multiple'):
                    choice_ids = request.POST.getlist(f'question_{question.id}')
                    selected_answers = ExamAnswer.objects.filter(question=question, id__in=choice_ids)
                    user_answer_obj.selected_answers.set(selected_answers)
                elif question_type == 'true_false':
                    choice_id = request.POST.get(f'question_{question.id}')
                    if choice_id:
                        answer = ExamAnswer.objects.filter(question=question, id=choice_id).first()
                        if answer:
                            user_answer_obj.selected_answers.set([answer])
                elif question_type == 'identification':
                    text_ans = request.POST.get(f'question_{question.id}_text', '').strip()
                    user_answer_obj.text_answer = text_ans
                
                user_answer_obj.check_answer()
                user_answer_obj.save()
                total_points += question.points
                if user_answer_obj.is_correct:
                    total_score += question.points

            exam_score = (total_score / total_points) * 100 if total_points > 0 else 0
            user_attempt.raw_points = total_score
            user_attempt.total_points = total_points
            user_attempt.score = exam_score
            user_attempt.completed = True
            user_attempt.passed = exam_score >= exam.passing_score
            user_attempt.end_time = timezone.now()
            user_attempt.save()
            messages.success(request, f"Exam submitted! Your score: {user_attempt.raw_points}/{user_attempt.total_points} points ({user_attempt.score:.2f}%)")
            return redirect('exams:exam_results', attempt_id=user_attempt.id)

    questions = exam.get_ordered_questions()
    return render(request, 'exams/take.html', {
        'exam': exam,
        'questions': questions,
        'user_attempt': user_attempt,
    })

@login_required
def exam_results(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    exam = attempt.exam
    user_answers = attempt.user_answers.select_related('question').prefetch_related('selected_answers')
    return render(request, 'exams/results.html', {
        'exam': exam,
        'attempt': attempt,
        'user_answers': user_answers
    })

@login_required
def exam_history(request):
    attempts_qs = ExamAttempt.objects.filter(user=request.user).select_related('exam').order_by('-start_time')
    paginator = Paginator(attempts_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'exams/history.html', {'page_obj': page_obj})

@login_required
def archive_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:view_exam', exam_id=exam_id)
    messages.success(request, "Exam archived.")
    return redirect('exams:grading_period_exam_list')

@login_required
def unarchive_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:view_exam', exam_id=exam_id)
    messages.success(request, "Exam unarchived.")
    return redirect('exams:grading_period_exam_list')

@login_required
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:view_exam', exam_id=exam_id)
    
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES, instance=exam)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Exam updated successfully.")
                return redirect('exams:view_exam', exam_id=exam.id)
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = ExamForm(instance=exam)
    return render(request, 'exams/edit.html', {'form': form, 'exam': exam})

@login_required
def delete_exam_question(request, exam_id, question_id):
    exam = get_object_or_404(Exam, id=exam_id)
    question = get_object_or_404(ExamQuestion, id=question_id, exam=exam)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:add_exam_questions', exam_id=exam.id)
    question.delete()
    messages.success(request, "Question deleted.")
    return redirect('exams:add_exam_questions', exam_id=exam.id)

@login_required
def lock_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:view_exam', exam_id=exam_id)
    exam.locked = True
    exam.save(update_fields=['locked'])
    messages.success(request, "Exam locked.")
    return redirect('exams:view_exam', exam_id=exam_id)

@login_required
def unlock_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('exams:view_exam', exam_id=exam_id)
    exam.locked = False
    exam.save(update_fields=['locked'])
    messages.success(request, "Exam unlocked.")
    return redirect('exams:view_exam', exam_id=exam_id)

@staff_member_required  # from django.contrib.admin.views.decorators!
def toggle_period_lock(request, grading_period):
    exam = Exam.objects.filter(grading_period=grading_period).first()
    if exam:
        exam.locked = not exam.locked
        exam.save(update_fields=['locked'])
        if exam.locked:
            messages.success(request, f"{dict(EXAM_GRADING_PERIOD_CHOICES).get(grading_period, grading_period)} exam locked.")
        else:
            messages.success(request, f"{dict(EXAM_GRADING_PERIOD_CHOICES).get(grading_period, grading_period)} exam unlocked.")
    else:
        messages.error(request, "No exam for this grading period.")
    return HttpResponseRedirect(reverse('exams:grading_period_exam_list'))
