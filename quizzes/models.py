from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time_limit = models.PositiveIntegerField(
        help_text="Time limit in minutes (0 for no limit)",
        default=0
    )
    passing_score = models.PositiveIntegerField(
        help_text="Percentage required to pass",
        default=70
    )
    is_active = models.BooleanField(default=True)
    shuffle_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(
        help_text="Show correct answers after submission",
        default=True
    )

    class Meta:
        verbose_name_plural = "quizzes"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('quiz_detail', kwargs={'pk': self.pk})

    def question_count(self):
        return self.questions.count()

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text[:50]}..." if len(self.text) > 50 else self.text

class QuizAttempt(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def calculate_score(self):
        correct_answers = self.user_answers.filter(is_correct=True).count()
        total_questions = self.quiz.question_count()
        self.score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        self.passed = self.score >= self.quiz.passing_score
        self.save()
        return self.score

class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_user_answers')
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True, related_name='quiz_user_selected_answers')
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')
