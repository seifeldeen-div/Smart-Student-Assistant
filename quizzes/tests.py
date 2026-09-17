from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from courses.models import Course
from notifications.models import TaskNotification

from .models import Question, Quiz, StudentAnswer, StudentQuizAttempt


class QuizWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="quiz-instructor", password="secret123")
        self.student = User.objects.create_user(username="quiz-student", password="secret123")
        self.other_instructor = User.objects.create_user(username="other-quiz-instructor", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.other_instructor, role="instructor")
        self.course = Course.objects.create(name="Algorithms", instructor=self.instructor)
        self.course.students.add(self.student)
        start = timezone.now() - timedelta(minutes=5)
        end = timezone.now() + timedelta(minutes=30)
        self.quiz = Quiz.objects.create(
            course=self.course,
            title="Sorting basics",
            duration=10,
            start_time=start,
            end_time=end,
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text="Which algorithm is stable?",
            option_a="Merge sort",
            option_b="Heap sort",
            option_c="Selection sort",
            option_d="Quick sort",
            correct_option="a",
            marks=2,
        )
        self.quiz.recalculate_total_marks()

    def test_student_submission_is_graded_and_reviewed(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("quiz_attempt", args=[self.quiz.pk]),
            {f"question_{self.question.pk}": "a"},
        )

        attempt = StudentQuizAttempt.objects.get(quiz=self.quiz, student=self.student)
        self.assertRedirects(response, reverse("quiz_review", args=[attempt.pk]))
        self.assertTrue(attempt.completed)
        self.assertEqual(attempt.score, 2)
        self.assertEqual(StudentAnswer.objects.get(attempt=attempt).selected_option, "a")

        review = self.client.get(reverse("quiz_review", args=[attempt.pk]))
        self.assertContains(review, "Correct")
        self.assertContains(review, "100")

    def test_instructor_can_review_attempt_but_other_instructor_cannot(self):
        attempt = StudentQuizAttempt.objects.create(
            quiz=self.quiz,
            student=self.student,
            score=0,
            submitted_at=timezone.now(),
            completed=True,
        )
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("instructor_quiz_submissions", args=[self.quiz.pk]))
        self.assertContains(response, "quiz-student")
        detail = self.client.get(reverse("instructor_attempt_detail", args=[attempt.pk]))
        self.assertEqual(detail.status_code, 200)

        self.client.force_login(self.other_instructor)
        self.assertEqual(self.client.get(reverse("instructor_quiz_submissions", args=[self.quiz.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("instructor_attempt_detail", args=[attempt.pk])).status_code, 404)

    def test_open_quiz_notifies_each_enrolled_student(self):
        self.client.force_login(self.student)
        self.client.get(reverse("quiz_list"))

        notification = TaskNotification.objects.get(recipient=self.student, quiz=self.quiz)
        self.assertEqual(notification.message, "Quiz 'Sorting basics' is now open for course 'Algorithms'!")
        self.assertEqual(TaskNotification.objects.filter(recipient=self.student, quiz=self.quiz).count(), 1)

    def test_instructor_cannot_create_quiz_for_another_instructors_course(self):
        other_course = Course.objects.create(name="Private Algorithms", instructor=self.other_instructor)
        self.client.force_login(self.instructor)

        response = self.client.get(reverse("quiz_create", args=[other_course.pk]))

        self.assertEqual(response.status_code, 404)