from django.db import models
from django.contrib.auth.models import User
from courses.models import Course

class Task(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("done", "Done")]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
