from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="taught_courses")
    students = models.ManyToManyField(User, related_name="enrolled_courses", blank=True)

    def __str__(self):
        return self.name
