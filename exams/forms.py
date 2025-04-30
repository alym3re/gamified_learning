from django import forms
from .models import Exam
from quizzes.models import Question

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'description', 'duration', 'passing_score', 'shuffle_questions', 'show_results']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ExamQuestionForm(forms.Form):
    question = forms.ModelChoiceField(
        queryset=Question.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    points = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        question_queryset = kwargs.pop('question_queryset', None)
        super().__init__(*args, **kwargs)
        if question_queryset:
            self.fields['question'].queryset = question_queryset