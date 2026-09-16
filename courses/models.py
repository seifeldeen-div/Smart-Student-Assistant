from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Course(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="taught_courses",
        limit_choices_to={"profile__role": "instructor"},
    )
    schedule = models.CharField(max_length=255, blank=True)
    students = models.ManyToManyField(User, related_name="enrolled_courses", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["instructor"]),
            models.Index(fields=["name"]),
        ]

    def clean(self):
        super().clean()
        if self.instructor_id:
            profile = getattr(self.instructor, "profile", None)
            if not (profile and profile.role == "instructor") and not self.instructor.is_superuser:
                raise ValidationError({"instructor": "Courses must be owned by an instructor."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
