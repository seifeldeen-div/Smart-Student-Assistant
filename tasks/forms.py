from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from courses.models import Course
from .models import Task
from .models import StudentNote, TaskSubmission


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["course", "assigned_to", "title", "description", "due_date", "status", "priority"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "status": forms.Select(),
            "priority": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not self.user:
            return
        role = _role(self.user)
        is_admin = self.user.is_superuser or role == "admin"

        if role == "student" and not is_admin:
            self.fields.pop("assigned_to")
            self.fields["course"].queryset = Course.objects.filter(students=self.user)
        else:
            if is_admin:
                self.fields["course"].queryset = Course.objects.all()
                self.fields["assigned_to"].queryset = User.objects.filter(profile__role="student")
            else:
                self.fields["course"].queryset = Course.objects.filter(instructor=self.user)
                self.fields["assigned_to"].queryset = User.objects.filter(
                    profile__role="student",
                    enrolled_courses__instructor=self.user,
                ).distinct()
            self.fields["assigned_to"].required = False
            self.fields["assigned_to"].label = "Assign to student"
            self.fields["assigned_to"].empty_label = "Personal task (no student)"
            if not self.fields["assigned_to"].queryset.exists():
                self.fields["assigned_to"].help_text = "No students are available yet. Enrol students into your courses first (Courses → Students)."
            else:
                self.fields["assigned_to"].help_text = "Pick a student to assign this task, or leave it blank for a personal task."

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < timezone.localdate():
            raise ValidationError("Due date must be today or in the future.")
        return due_date

    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            return cleaned_data

        role = _role(self.user)
        is_admin = self.user.is_superuser or role == "admin"
        course = cleaned_data.get("course")
        assigned_to = cleaned_data.get("assigned_to")

        if role == "student" and not is_admin:
            cleaned_data["assigned_to"] = None
            if course and not course.students.filter(id=self.user.id).exists():
                raise ValidationError("You can only assign a task to a course you are enrolled in.")
            return cleaned_data

        if assigned_to and not is_admin:
            taught = Course.objects.filter(instructor=self.user)
            if course:
                if course.instructor_id != self.user.id:
                    raise ValidationError({"course": "You can only create tasks for your own courses."})
                if not course.students.filter(id=assigned_to.id).exists():
                    raise ValidationError({"assigned_to": "Assign the task only to a student enrolled in the selected course."})
            elif not taught.filter(students=assigned_to).exists():
                raise ValidationError({"assigned_to": "You can only assign tasks to students enrolled in your courses."})
        return cleaned_data


class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ["submission_file", "submission_link", "notes"]

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("submission_file") and not cleaned_data.get("submission_link"):
            raise ValidationError("Upload a file or provide a submission link.")
        return cleaned_data


class StudentNoteForm(forms.ModelForm):
    class Meta:
        model = StudentNote
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a study note..."}),
        }

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if not content:
            raise ValidationError("Note content is required.")
        return contentg