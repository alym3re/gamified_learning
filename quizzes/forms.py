from django import forms
from .models import Quiz, Question, Answer, QUESTION_TYPE_CHOICES


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'grading_period', 'time_limit', 'passing_score',
            'shuffle_questions', 'show_correct_answers', 'is_archived', 'thumbnail'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'grading_period': forms.Select(attrs={'class': 'form-select'}),
            'time_limit': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control'}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_correct_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_archived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'explanation', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MultipleChoiceAnswerForm(AnswerForm):
    """Form for multiple choice answers where only one answer can be correct"""
    pass

class MultipleAnswerForm(AnswerForm):
    """Form for multiple answer questions where multiple answers can be correct"""
    pass

class TrueFalseAnswerForm(AnswerForm):
    """Form specifically for True/False questions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Select(
            choices=[('True', 'True'), ('False', 'False')],
            attrs={'class': 'form-select'}
        )

class ShortAnswerForm(AnswerForm):
    """Form for short answer questions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_correct'].widget = forms.HiddenInput()
        self.fields['is_correct'].initial = True

# Base formset for answers
AnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=AnswerForm, extra=2, can_delete=True, min_num=2
)

# Specialized formsets for different question types
MultipleChoiceFormSet = forms.inlineformset_factory(
    Question, Answer, form=MultipleChoiceAnswerForm, extra=4, can_delete=True, min_num=2
)

MultipleAnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=MultipleAnswerForm, extra=4, can_delete=True, min_num=2
)

TrueFalseFormSet = forms.inlineformset_factory(
    Question, Answer, form=TrueFalseAnswerForm, extra=2, can_delete=True, min_num=2, max_num=2
)

ShortAnswerFormSet = forms.inlineformset_factory(
    Question, Answer, form=ShortAnswerForm, extra=1, can_delete=True, min_num=1, max_num=1
)

# Factory function to get the appropriate formset based on question type
def get_answer_formset_for_question_type(question_type):
    formset_map = {
        'multiple_choice': MultipleChoiceFormSet,
        'multiple_answer': MultipleAnswerFormSet,
        'true_false': TrueFalseFormSet,
        'short_answer': ShortAnswerFormSet,
    }
    return formset_map.get(question_type, AnswerFormSet)
