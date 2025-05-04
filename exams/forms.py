from django import forms
from .models import Exam, ExamQuestion, ExamAnswer, EXAM_QUESTION_TYPE_CHOICES

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'grading_period', 'time_limit', 'passing_score',
            'shuffle_questions', 'show_correct_answers'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'grading_period': forms.Select(attrs={'class': 'form-select'}),
            'time_limit': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control'}),
            'shuffle_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_correct_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExamQuestionForm(forms.ModelForm):
    class Meta:
        model = ExamQuestion
        fields = ['text', 'question_type', 'explanation', 'points', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }

class ExamAnswerForm(forms.ModelForm):
    class Meta:
        model = ExamAnswer
        fields = ['text', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExamMultipleChoiceAnswerForm(ExamAnswerForm):
    """Form for multiple choice answers where only one answer can be correct"""
    pass

class ExamMultipleAnswerForm(ExamAnswerForm):
    """Form for multiple answer questions where multiple answers can be correct"""
    pass

class ExamTrueFalseAnswerForm(ExamAnswerForm):
    """Form specifically for True/False questions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget = forms.Select(
            choices=[('True', 'True'), ('False', 'False')],
            attrs={'class': 'form-select'}
        )

class ExamShortAnswerForm(ExamAnswerForm):
    """Form for short answer/identification questions"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_correct'].widget = forms.HiddenInput()
        self.fields['is_correct'].initial = True

ExamAnswerFormSet = forms.inlineformset_factory(
    ExamQuestion, ExamAnswer, form=ExamAnswerForm, extra=2, can_delete=True, min_num=2
)

ExamMultipleChoiceFormSet = forms.inlineformset_factory(
    ExamQuestion, ExamAnswer, form=ExamMultipleChoiceAnswerForm, extra=4, can_delete=True, min_num=2, max_num=4
)

ExamMultipleAnswerFormSet = forms.inlineformset_factory(
    ExamQuestion, ExamAnswer, form=ExamMultipleAnswerForm, extra=4, can_delete=True, min_num=2, max_num=4
)

ExamTrueFalseFormSet = forms.inlineformset_factory(
    ExamQuestion, ExamAnswer, form=ExamTrueFalseAnswerForm, extra=2, can_delete=True, min_num=2, max_num=2
)

ExamShortAnswerFormSet = forms.inlineformset_factory(
    ExamQuestion, ExamAnswer, form=ExamShortAnswerForm, extra=1, can_delete=True, min_num=1, max_num=1
)

def get_answer_formset_for_question_type(question_type):
    """
    Returns the appropriate answer formset class for a given question type.
    
    This function maps question types to their corresponding formset classes,
    ensuring compatibility across the application. It handles both 'short_answer'
    and 'identification' as synonyms for the same formset type.
    
    Args:
        question_type (str): The type of question (e.g., 'multiple_choice', 'true_false')
        
    Returns:
        FormSet: The appropriate formset class for the question type
    """
    formset_map = {
        'multiple_choice': ExamMultipleChoiceFormSet,
        'multiple_answer': ExamMultipleAnswerFormSet,
        'true_false': ExamTrueFalseFormSet,
        'short_answer': ExamShortAnswerFormSet,
        'identification': ExamShortAnswerFormSet,  # Added for compatibility
    }
    return formset_map.get(question_type, ExamAnswerFormSet)
