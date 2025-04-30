from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import JsonResponse
from .models import Quiz, Question, Answer, QuizAttempt, UserAnswer
from .forms import QuizForm, QuestionForm, AnswerForm, AnswerFormSet

@login_required
def quiz_list(request):
    quizzes = Quiz.objects.filter(is_active=True)
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz')
    return render(request, 'quizzes/list.html', {
        'quizzes': quizzes,
        'attempts': attempts
    })

@login_required
def create_quiz(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to create quizzes.")
        return redirect('quiz_list')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect('add_quiz_questions', quiz_id=quiz.id)
    else:
        form = QuizForm()
    return render(request, 'quizzes/create.html', {'form': form})

@login_required
def add_quiz_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not request.user.is_staff or quiz.created_by != request.user:
        messages.error(request, "You don't have permission to edit this quiz.")
        return redirect('quiz_list')
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        answer_formset = AnswerFormSet(request.POST, prefix='answers')
        
        if question_form.is_valid() and answer_formset.is_valid():
            with transaction.atomic():
                question = question_form.save(commit=False)
                question.quiz = quiz
                question.save()
                
                answers = answer_formset.save(commit=False)
                for answer in answers:
                    answer.question = question
                    answer.save()
                
                # Check if at least one correct answer exists
                if not any(answer.is_correct for answer in answers):
                    messages.error(request, "At least one answer must be marked as correct.")
                    raise forms.ValidationError("At least one answer must be marked as correct.")
                
                messages.success(request, 'Question added successfully!')
                return redirect('add_quiz_questions', quiz_id=quiz.id)
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
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    
    # Check for existing incomplete attempt
    attempt = QuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        completed=False
    ).first()
    
    if not attempt:
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz
        )
    
    if request.method == 'POST':
        with transaction.atomic():
            correct_answers = 0
            total_questions = quiz.questions.count()
            
            for question in quiz.questions.all():
                answer_id = request.POST.get(f'question_{question.id}')
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
                    question=question,
                    selected_answer=selected_answer,
                    is_correct=is_correct
                )
            
            attempt.completed = True
            attempt.end_time = timezone.now()
            attempt.score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
            attempt.passed = attempt.score >= quiz.passing_score
            attempt.save()
            
            messages.success(request, 'Quiz submitted successfully!')
            return redirect('quiz_results', attempt_id=attempt.id)
    
    questions = quiz.questions.all().prefetch_related('answers')
    if quiz.shuffle_questions:
        questions = list(questions)
        import random
        random.shuffle(questions)
    
    return render(request, 'quizzes/take.html', {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'time_limit': quiz.time_limit * 60 if quiz.time_limit > 0 else None
    })

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    if not attempt.completed:
        messages.error(request, "This quiz attempt is not completed yet.")
        return redirect('quiz_list')
    
    user_answers = {
        ua.question_id: ua 
        for ua in attempt.user_answers.select_related('question', 'selected_answer')
    }
    
    return render(request, 'quizzes/results.html', {
        'attempt': attempt,
        'user_answers': user_answers,
        'show_answers': attempt.quiz.show_correct_answers
    })

@login_required
def quiz_history(request):
    attempts = QuizAttempt.objects.filter(
        user=request.user,
        completed=True
    ).select_related('quiz').order_by('-start_time')
    
    return render(request, 'quizzes/history.html', {
        'attempts': attempts
    })

@login_required
def delete_question(request, quiz_id, question_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if not request.user.is_staff or quiz.created_by != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    question.delete()
    return JsonResponse({'success': True})