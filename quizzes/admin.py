
from django.contrib import admin

from .models import Quiz, Question, Answer, QuizAttempt, UserAnswer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    min_num = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    inlines = [AnswerInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'is_active', 'question_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    inlines = [QuestionInline]

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Questions'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'points', 'answer_count')
    list_filter = ('quiz',)
    search_fields = ('text', 'quiz__title')
    inlines = [AnswerInline]

    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = 'Answers'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('text', 'question__text')

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'end_time', 'completed')
    list_filter = ('quiz', 'end_time', 'completed', 'user')
    search_fields = ('user__username', 'quiz__title')

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'question', 'selected_answer', 'is_correct')
    list_filter = ('question', 'is_correct', 'attempt__user')
    search_fields = ('attempt__user__username', 'question__text', 'selected_answer__text')

    def get_user(self, obj):
        return obj.attempt.user
    get_user.short_description = 'User'
    get_user.admin_order_field = 'attempt__user'

# NOTE: To fix reverse accessor clashes, update your UserAnswer model ForeignKeys:
# question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_user_answers')
# selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='quiz_user_answers_selected')
