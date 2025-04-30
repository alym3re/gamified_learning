from django.urls import path
from . import views

urlpatterns = [
    path('', views.lesson_list, name='lesson_list'),
    path('upload/', views.upload_lesson, name='upload_lesson'),
    path('categories/', views.manage_categories, name='manage_categories'),
    path('<slug:slug>/', views.view_lesson, name='view_lesson'),
    path('<slug:slug>/complete/', views.mark_completed, name='mark_completed'),
]