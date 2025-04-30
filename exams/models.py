from django.db import models
from django.contrib.auth import get_user_model
from quizzes.models import Question
from django.utils import timezone

class Exam(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    passing_score = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shuffle_questions = models.BooleanField(default=False)
    show_results = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class ExamAttempt(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def duration(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None

    def __str__(self):
        return f"{self.user.username} - {self.exam.title}"

class UserAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey('quizzes.Answer', on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')