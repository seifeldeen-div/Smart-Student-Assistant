from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from courses.models import Course

class Task(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="low")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["course"]),
            models.Index(fields=["due_date"]),
        ]

    def clean(self):
        super().clean()
        if self.owner_id:
            profile = getattr(self.owner, "profile", None)
            if not (profile and profile.role == "student") and not self.owner.is_superuser:
                raise ValidationError({"owner": "Tasks must be owned by a student."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
