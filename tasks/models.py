from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from courses.models import Course


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


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
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        verbose_name="Assigned student",
    )
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
        owner = self.owner if self.owner_id else None
        owner_role = _role(owner) if owner else None
        is_admin = bool(owner and (owner.is_superuser or owner_role == "admin"))

        if self.owner_id and owner_role not in {"student", "instructor"} and not is_admin:
            raise ValidationError({"owner": f"Tasks must be owned by a student or an instructor. Current owner role is: {owner_role or 'none'}."})

        if self.assigned_to_id:
            if _role(self.assigned_to) != "student":
                raise ValidationError({"assigned_to": "Tasks can only be assigned to a student."})
            if not self.owner_id:
                return
            if owner_role != "instructor" and not is_admin:
                who = owner.get_username()
                raise ValidationError({"assigned_to": f"Only instructors or admins can assign tasks to students. Task owner '{who}' has role '{owner_role or 'none'}'."})
            if not is_admin:
                if self.course_id:
                    if self.course.instructor_id != self.owner_id:
                        raise ValidationError({"course": "You can only assign tasks for your own courses."})
                    if not self.course.students.filter(id=self.assigned_to_id).exists():
                        raise ValidationError({"assigned_to": "The selected student is not enrolled in this course."})
                elif not Course.objects.filter(instructor=self.owner, students=self.assigned_to).exists():
                    raise ValidationError({"assigned_to": "You can only assign tasks to students enrolled in your courses."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class TaskSubmission(models.Model):
    STATUS_CHOICES = [
        ("Submitted", "Submitted"),
        ("Graded", "Graded"),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_submissions")
    submission_file = models.FileField(upload_to="submissions/", blank=True)
    submission_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Submitted")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["task", "student"], name="unique_task_submission_per_student"),
        ]
        ordering = ["-submitted_at"]

    def clean(self):
        super().clean()
        if not self.submission_file and not self.submission_link:
            raise ValidationError("Submit a file or a URL link.")
        if self.student_id and self.task_id and self.task.course_id:
            if not self.task.course.students.filter(id=self.student_id).exists():
                raise ValidationError("Only enrolled students can submit this task.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class StudentNote(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_notes")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["is_completed", "-created_at"]
        indexes = [
            models.Index(fields=["student", "is_completed"]),
        ]

    def __str__(self):
        return self.content[:60]