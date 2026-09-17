from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from courses.models import Course


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="managed_quizzes")
    title = models.CharField(max_length=150)
    duration = models.PositiveIntegerField(help_text="Duration in minutes.")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_marks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time", "id"]
        indexes = [
            models.Index(fields=["course", "start_time", "end_time"]),
        ]

    def clean(self):
        super().clean()
        if self.end_time <= self.start_time:
            raise ValidationError({"end_time": "The end time must be after the start time."})

    @property
    def is_open(self):
        current_time = timezone.now()
        return self.start_time <= current_time <= self.end_time

    @property
    def question_total_marks(self):
        return self.questions.aggregate(total=models.Sum("marks"))["total"] or 0

    def recalculate_total_marks(self):
        total = self.question_total_marks
        if self.total_marks != total:
            Quiz.objects.filter(pk=self.pk).update(total_marks=total)
            self.total_marks = total
        return total

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
    text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    marks = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def option_text(self, option):
        return getattr(self, f"option_{option}", "")

    def __str__(self):
        return self.text[:80]


class StudentQuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "student"], name="unique_student_quiz_attempt"),
        ]

    @property
    def percentage(self):
        if not self.quiz.total_marks:
            return 0
        return round((self.score / self.quiz.total_marks) * 100, 2)

    def __str__(self):
        return f"{self.student} - {self.quiz}"


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(StudentQuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="student_answers")
    selected_option = models.CharField(max_length=1, choices=Question.OPTION_CHOICES, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_attempt_question_answer"),
        ]

    @property
    def is_correct(self):
        return self.selected_option == self.question.correct_option
