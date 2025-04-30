from django.db import models
from django.contrib.auth import get_user_model
import os

def lesson_file_path(instance, filename):
    return f'lesson_files/lesson_{instance.id}/{filename}'

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to=lesson_file_path)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()