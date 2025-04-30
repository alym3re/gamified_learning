from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_list, name='quiz_list'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/questions/', views.add_quiz_questions, name='add_quiz_questions'),
    path('<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('history/', views.quiz_history, name='quiz_history'),
    
    # AJAX endpoints
    path('<int:quiz_id>/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
]