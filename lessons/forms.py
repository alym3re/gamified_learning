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
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.ms-powerpoint'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'description': 'Description',
            'is_featured': 'Feature this lesson'
        }
        help_texts = {
            'file': 'Only .pdf, .doc, .docx files are allowed.',
            'thumbnail': 'Optional. Recommended size: 800x450px'
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        allowed_exts = ['.pdf', '.doc', '.docx', '.pptx']
        import os
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_exts:
            raise forms.ValidationError("Only PDF and Word (.doc/.docx) files are allowed.")
        return file