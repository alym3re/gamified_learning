from django.urls import path
from . import views
from .views import (
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomPasswordResetCompleteView
)

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    
    # Password reset URLs
    path('password-reset/', 
         CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('password-reset/done/', 
         CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]