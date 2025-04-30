from django.db import models
from django.contrib.auth import get_user_model

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit = models.IntegerField(help_text="Time limit in minutes", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    points = models.IntegerField(default=1)
    
    def __str__(self):
        return self.text[:50] + "..." if len(self.text) > 50 else self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text

class QuizAttempt(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user} - {self.quiz}"