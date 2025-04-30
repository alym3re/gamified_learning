from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Exam, ExamAttempt, ExamQuestion, UserAnswer
from .forms import ExamForm, ExamQuestionForm
from quizzes.models import Question, Answer

@login_required
def exam_list(request):
    exams = Exam.objects.filter(is_active=True)
    attempts = ExamAttempt.objects.filter(user=request.user, completed=True).select_related('exam')
    return render(request, 'exams/list.html', {
        'exams': exams,
        'attempts': attempts
    })

@login_required
def create_exam(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create exams.")
        return redirect('exam_list')
    
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.created_by = request.user
            exam.save()
            messages.success(request, 'Exam created successfully!')
            return redirect('add_exam_questions', exam_id=exam.id)
    else:
        form = ExamForm()
    return render(request, 'exams/create.html', {'form': form})

@login_required
def add_exam_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this exam.")
        return redirect('exam_list')
    
    existing_question_ids = exam.exam_questions.values_list('question_id', flat=True)
    available_questions = Question.objects.exclude(id__in=existing_question_ids)
    
    if request.method == 'POST':
        form = ExamQuestionForm(request.POST, question_queryset=available_questions)
        if form.is_valid():
            ExamQuestion.objects.create(
                exam=exam,
                question=form.cleaned_data['question'],
                points=form.cleaned_data['points']
            )
            messages.success(request, 'Question added to exam!')
            return redirect('add_exam_questions', exam_id=exam.id)
    else:
        form = ExamQuestionForm(question_queryset=available_questions)
    
    exam_questions = exam.exam_questions.select_related('question').order_by('order')
    return render(request, 'exams/add_questions.html', {
        'exam': exam,
        'form': form,
        'exam_questions': exam_questions
    })

@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id, is_active=True)
    
    # Check for existing incomplete attempt
    attempt = ExamAttempt.objects.filter(
        user=request.user,
        exam=exam,
        completed=False
    ).first()
    
    if not attempt:
        attempt = ExamAttempt.objects.create(
            user=request.user,
            exam=exam
        )
    
    if request.method == 'POST':
        with transaction.atomic():
            # Process exam submission
            correct_answers = 0
            total_questions = exam.exam_questions.count()
            
            for eq in exam.exam_questions.all():
                answer_id = request.POST.get(f'question_{eq.question.id}')
                selected_answer = None
                is_correct = False
                
                if answer_id:
                    try:
                        selected_answer = Answer.objects.get(id=answer_id)
                        is_correct = selected_answer.is_correct
                        if is_correct:
                            correct_answers += 1
                    except Answer.DoesNotExist:
                        pass
                
                UserAnswer.objects.create(
                    attempt=attempt,
                    question=eq.question,
                    selected_answer=selected_answer,
                    is_correct=is_correct
                )
            
            attempt.completed = True
            attempt.end_time = timezone.now()
            attempt.score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            attempt.passed = attempt.score >= exam.passing_score
            attempt.save()
            
            messages.success(request, 'Exam submitted successfully!')
            return redirect('exam_results', attempt_id=attempt.id)
    
    questions = exam.exam_questions.select_related('question').order_by('order')
    if exam.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)
    
    return render(request, 'exams/take.html', {
        'exam': exam,
        'attempt': attempt,
        'questions': questions
    })

@login_required
def exam_results(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    if not attempt.completed:
        messages.error(request, "This exam attempt is not completed yet.")
        return redirect('exam_list')
    
    return render(request, 'exams/results.html', {
        'attempt': attempt,
        'show_results': attempt.exam.show_results
    })

@login_required
def review_exam(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, user=request.user)
    if not attempt.completed:
        messages.error(request, "This exam attempt is not completed yet.")
        return redirect('exam_list')
    
    if not attempt.exam.show_results:
        messages.error(request, "Review is not allowed for this exam.")
        return redirect('exam_list')
    
    user_answers = {
        ua.question_id: ua 
        for ua in attempt.user_answers.select_related('question', 'selected_answer')
    }
    
    exam_questions = attempt.exam.exam_questions.select_related('question').order_by('order')
    
    return render(request, 'exams/review.html', {
        'attempt': attempt,
        'exam_questions': exam_questions,
        'user_answers': user_answers
    })