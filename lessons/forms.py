from django import forms
from .models import Lesson, GRADING_PERIOD_CHOICES

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'grading_period', 'file', 'thumbnail', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'grading_period': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'file', 'thumbnail', 'grading_period', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 7}),
        }
        labels = {
            'description': 'Description (Markdown supported)',
            'is_featured': 'Feature this lesson'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = True
        self.fields['thumbnail'].help_text = "Optional. Recommended size: 800x450px"