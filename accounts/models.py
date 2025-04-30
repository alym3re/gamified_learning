from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
import os

def profile_pic_path(instance, filename):
    return f'profile_pics/user_{instance.id}/{filename}'

class User(AbstractUser):
    student_id = models.CharField(max_length=20, unique=True)
    middle_name = models.CharField(max_length=50, blank=True)
    profile_pic = models.ImageField(upload_to=profile_pic_path, blank=True, null=True)
    points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.student_id})"
    
    def get_full_name(self):
        middle = f" {self.middle_name} " if self.middle_name else " "
        return f"{self.first_name}{middle}{self.last_name}"
    
    def get_absolute_url(self):
        return reverse('profile')
    
    def save(self, *args, **kwargs):
        # Delete old profile pic when updating
        try:
            old = User.objects.get(id=self.id)
            if old.profile_pic and old.profile_pic != self.profile_pic:
                old.profile_pic.delete(save=False)
        except User.DoesNotExist:
            pass
        super().save(*args, **kwargs)