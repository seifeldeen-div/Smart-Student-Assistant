from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from courses.models import Course
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["course", "title", "description", "due_date", "status", "priority"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "status": forms.Select(),
            "priority": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            is_admin = self.user.is_superuser or getattr(getattr(self.user, "profile", None), "role", None) == "admin"
            if is_admin:
                self.fields["course"].queryset = Course.objects.all()
            else:
                self.fields["course"].queryset = Course.objects.filter(students=self.user)

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < timezone.localdate():
            raise ValidationError("Due date must be today or in the future.")
        return due_date

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        if course and self.user and not self.user.is_superuser and not course.students.filter(id=self.user.id).exists():
            raise ValidationError("You can only assign a task to a course you are enrolled in.")
        return cleaned_data