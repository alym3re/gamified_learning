from django import forms
from .models import Lesson, LessonCategory

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'description', 'content', 'file', 
            'thumbnail', 'category', 'difficulty', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'is_featured': 'Feature this lesson on homepage'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = True
        self.fields['thumbnail'].help_text = "Optional. Recommended size: 800x450px"

class LessonCategoryForm(forms.ModelForm):
    class Meta:
        model = LessonCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'icon': forms.TextInput(attrs={
                'placeholder': 'Example: fas fa-book'
            })
        }