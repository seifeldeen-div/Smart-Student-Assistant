from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from courses.models import Course
from notifications.models import TaskNotification
from tasks.models import Task


class NotificationFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.instructor = User.objects.create_user(username="inst_n", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.student = User.objects.create_user(username="stu_n", password="secret123")
        Profile.objects.create(user=self.student, role="student")

        self.other_student = User.objects.create_user(username="stu2_n", password="secret123")
        Profile.objects.create(user=self.other_student, role="student")

        self.course = Course.objects.create(
            name="Web Development",
            description="Course description",
            instructor=self.instructor,
        )
        self.course.students.add(self.student)
        self.course.students.add(self.other_student)

    def _create_assigned_task(self, assigned_to=None, title="HTML Assignment"):
        return Task.objects.create(
            owner=self.instructor,
            course=self.course,
            assigned_to=assigned_to or self.student,
            title=title,
            status="pending",
        )

    def test_student_gets_notified_when_task_assigned(self):
        self.client.login(username="inst_n", password="secret123")
        self.client.post(reverse("task_create"), {
            "title": "HTML Assignment",
            "course": self.course.pk,
            "assigned_to": self.student.pk,
            "priority": "high",
            "status": "pending",
        })

        notification = TaskNotification.objects.filter(recipient=self.student, is_read=False).first()
        self.assertIsNotNone(notification)
        self.assertIn("HTML Assignment", notification.message)
        self.assertIn(self.instructor.get_username(), notification.message)

    def test_instructor_gets_notified_when_student_completes(self):
        task = self._create_assigned_task()
        TaskNotification.objects.filter(recipient=self.student).delete()

        self.client.login(username="stu_n", password="secret123")
        self.client.post(reverse("task_complete", args=[task.pk]))

        notification = TaskNotification.objects.filter(recipient=self.instructor, is_read=False).first()
        self.assertIsNotNone(notification)
        self.assertIn(self.student.get_username(), notification.message)
        self.assertIn("HTML Assignment", notification.message)

    def test_reassigning_task_notifies_only_new_student(self):
        task = self._create_assigned_task()
        TaskNotification.objects.all().delete()

        self.client.login(username="inst_n", password="secret123")
        self.client.post(reverse("task_update", args=[task.pk]), {
            "title": "HTML Assignment",
            "course": self.course.pk,
            "assigned_to": self.other_student.pk,
            "priority": "low",
            "status": "pending",
        })

        self.assertEqual(TaskNotification.objects.filter(recipient=self.other_student).count(), 1)
        self.assertEqual(TaskNotification.objects.filter(recipient=self.student).count(), 0)

    def test_model_create_fires_assignment_notification(self):
        self._create_assigned_task()
        self.assertEqual(TaskNotification.objects.filter(recipient=self.student).count(), 1)

    def test_mark_notification_as_read(self):
        notification = TaskNotification.objects.create(recipient=self.student, task=None, message="Hello")
        self.client.login(username="stu_n", password="secret123")
        self.client.post(reverse("notification_mark_read", args=[notification.pk]))

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_notifications_as_read(self):
        for _ in range(3):
            TaskNotification.objects.create(recipient=self.student, task=None, message="Hi")

        self.client.login(username="stu_n", password="secret123")
        self.client.post(reverse("notification_mark_all_read"))

        self.assertEqual(TaskNotification.objects.filter(recipient=self.student, is_read=False).count(), 0)

    def test_cannot_read_another_users_notification(self):
        notification = TaskNotification.objects.create(recipient=self.student, task=None, message="Private")
        self.client.login(username="stu2_n", password="secret123")
        response = self.client.post(reverse("notification_mark_read", args=[notification.pk]))

        self.assertEqual(response.status_code, 404)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_notification_list_shows_only_own_notifications(self):
        TaskNotification.objects.create(recipient=self.student, task=None, message="For stu_n")
        TaskNotification.objects.create(recipient=self.other_student, task=None, message="For stu2_n")

        self.client.login(username="stu_n", password="secret123")
        response = self.client.get(reverse("notification_list"))

        self.assertContains(response, "For stu_n")
        self.assertNotContains(response, "For stu2_n")

    def test_unread_count_badge_shown_in_navbar(self):
        TaskNotification.objects.create(recipient=self.student, task=None, message="A")
        TaskNotification.objects.create(recipient=self.student, task=None, message="B", is_read=True)

        self.client.login(username="stu_n", password="secret123")
        response = self.client.get(reverse("task_list"))

        self.assertContains(response, 'class="nav-badge">1</span>')