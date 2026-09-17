from django import forms

from .models import Question, Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "duration", "start_time", "end_time"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S%z"]
        self.fields["end_time"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S%z"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = [
            "text", "option_a", "option_b", "option_c", "option_d", "correct_option", "marks",
        ]
