from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import os

def lesson_file_path(instance, filename):
    return f'lesson_files/lesson_{instance.id}/{filename}'

class LessonCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")

    class Meta:
        verbose_name_plural = "Lesson Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    content = models.TextField(blank=True)
    file = models.FileField(upload_to=lesson_file_path)
    thumbnail = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
    category = models.ForeignKey(LessonCategory, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='beginner')

    class Meta:
        ordering = ['-upload_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug or self.__class__.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            original_slug = slugify(self.title)
            slug = original_slug
            num = 1
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{original_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()

    def increment_view_count(self):
        self.view_count += 1
        self.save()

class LessonProgress(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_viewed = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = "Lesson Progress"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"
