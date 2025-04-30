from django import forms
from .models import Quiz, Question, Answer

class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit', 'passing_score', 
                 'shuffle_questions', 'show_correct_answers', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'time_limit': forms.NumberInput(attrs={'min': 0}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'explanation', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
            'explanation': forms.Textarea(attrs={'rows': 2}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(),
        }

AnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=AnswerForm, extra=1, can_delete=True, min_num=2
)