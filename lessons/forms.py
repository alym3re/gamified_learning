from django import forms
from .models import Lesson, GRADING_PERIOD_CHOICES

class LessonForm(forms.ModelForm):
    grading_period = forms.ChoiceField(
        choices=GRADING_PERIOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Grading Period'
    )

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