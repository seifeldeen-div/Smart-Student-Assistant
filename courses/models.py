from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

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


class AcademicTopic(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Quiz(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    topic = models.ForeignKey(AcademicTopic, on_delete=models.PROTECT, related_name="quizzes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["course"]),
            models.Index(fields=["topic"]),
        ]

    def __str__(self):
        return self.title


class Question(models.Model):
    OPTION_CHOICES = [
        ("a", "Option A"),
        ("b", "Option B"),
        ("c", "Option C"),
        ("d", "Option D"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    prompt = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)

    def __str__(self):
        return self.prompt[:60]


class QuizSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_submissions")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="submissions")
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["student", "quiz"]),
            models.Index(fields=["student", "completed_at"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.quiz} - {self.score}%"
