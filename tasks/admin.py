from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from .models import Task


class TaskAdminForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["owner"].required = False
        self.fields["owner"].help_text = (
            "Who created the task: the instructor who assigns it, or the student who owns their own task. "
            "When adding from the admin panel this defaults to the current user."
        )
        self.fields["assigned_to"].queryset = User.objects.filter(profile__role="student")
        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].label = "Assigned student"
        self.fields["assigned_to"].help_text = "The student this task is assigned to. Leave empty for a personal task."
        self.fields["course"].help_text = "Optional course the task belongs to."


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    list_display = ("title", "owner", "assigned_to", "course", "status", "priority", "due_date", "created_at")
    list_filter = ("status", "priority", "course")
    search_fields = ("title", "description")

    def save_model(self, request, obj, form, change):
        if not change and not obj.owner_id:
            obj.owner = request.user
        obj.save()