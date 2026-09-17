from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from courses.models import Course
from tasks.models import Task


class DashboardScopeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(username="student", password="secret123")
        self.other_student = User.objects.create_user(username="other", password="secret123")
        self.instructor = User.objects.create_user(username="instructor", password="secret123")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.other_student, role="student")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.course = Course.objects.create(name="Owned course", instructor=self.instructor)
        self.course.students.add(self.student)
        Task.objects.create(
            owner=self.student,
            course=self.course,
            title="Upcoming task",
            due_date=timezone.localdate() + timedelta(days=1),
            status="pending",
        )
        Task.objects.create(
            owner=self.other_student,
            title="Private task",
            status="completed",
        )

    def test_student_dashboard_metrics_are_owned_and_enrolled_only(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["dashboard_stats"]["total_tasks"], 1)
        self.assertEqual(response.context["dashboard_stats"]["pending_tasks"], 1)
        self.assertEqual(response.context["dashboard_stats"]["completed_tasks"], 0)
        self.assertEqual(list(response.context["dashboard_courses"]), [self.course])
        self.assertContains(response, "Upcoming task")
        self.assertNotContains(response, "Private task")

    def test_instructor_dashboard_excludes_unrelated_tasks(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["dashboard_activity"]["course_count"], 1)
        self.assertEqual(response.context["dashboard_activity"]["student_count"], 1)
        self.assertEqual(response.context["dashboard_activity"]["task_count"], 1)
        self.assertContains(response, "Upcoming task")
        self.assertNotContains(response, "Private task")
