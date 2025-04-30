from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('create/', views.create_exam, name='create_exam'),
    path('<int:exam_id>/questions/', views.add_exam_questions, name='add_exam_questions'),
    path('<int:exam_id>/take/', views.take_exam, name='take_exam'),
    path('results/<int:attempt_id>/', views.exam_results, name='exam_results'),
    path('review/<int:attempt_id>/', views.review_exam, name='review_exam'),
    
    # AJAX endpoints
    path('<int:exam_id>/questions/<int:eq_id>/delete/', views.delete_exam_question, name='delete_exam_question'),
    path('<int:exam_id>/questions/reorder/', views.reorder_questions, name='reorder_questions'),
]