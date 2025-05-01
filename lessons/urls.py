from django.urls import path
from . import views

app_name = "lessons"

urlpatterns = [
    path('', views.grading_period_list, name='grading_period_list'),
    path('period/<str:grading_period>/', views.lesson_list_by_period, name='lesson_list_by_period'),
    path('upload/', views.upload_lesson, name='upload_lesson'),
    path('<slug:slug>/', views.view_lesson, name='view_lesson'),
    path('<slug:slug>/complete/', views.mark_completed, name='mark_completed'),
    path('<slug:slug>/download/', views.download_lesson_file, name='download_lesson_file'),
    path('admin/lesson-access/', views.admin_lesson_access_report, name='lesson_access_report'),
]