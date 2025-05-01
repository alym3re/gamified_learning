from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

GRADING_PERIOD_CHOICES = [
    ('prelim', 'Prelim'),
    ('midterm', 'Midterm'),
    ('prefinal', 'Prefinal'),
    ('final', 'Final'),
]

def lesson_file_path(instance, filename):
    return f'lesson_files/lesson_{instance.id}/{filename}'

class Lesson(models.Model):
    grading_period = models.CharField(
        max_length=10, 
        choices=GRADING_PERIOD_CHOICES,
        default='prelim'  # Default moved here
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(help_text="Lesson description (Markdown supported)")
    file = models.FileField(upload_to=lesson_file_path)
    thumbnail = models.ImageField(upload_to='lesson_thumbnails/', blank=True, null=True)
    uploaded_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    upload_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

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
        import os
        name, extension = os.path.splitext(self.file.name)
        return extension.lower()

    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=["view_count"])

class LessonAccess(models.Model):
    ACCESS_TYPE_CHOICES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
    ]
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} {self.access_type} {self.lesson.title} on {self.timestamp}"

class LessonProgress(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    last_viewed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name_plural = "Lesson Progress"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"