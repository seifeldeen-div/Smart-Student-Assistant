from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from courses.models import Course
from tasks.models import Task


class AdminTaskFormCourseVisibilityTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_user(username="admin", password="secret123")
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

        Profile.objects.create(user=self.admin, role="admin")

        self.instructor = User.objects.create_user(username="instructor", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.course = Course.objects.create(
            name="Course 101",
            description="Course description",
            instructor=self.instructor,
        )

    def test_admin_can_see_all_courses_in_task_form_course_selector(self):
        self.client.login(username="admin", password="secret123")

        response = self.client.get(reverse("task_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Course 101")


class OwnershipFilteringTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.mohamed = User.objects.create_user(username="mohamed", password="secret123")
        self.ahmed = User.objects.create_user(username="ahmed", password="secret123")
        self.instructor = User.objects.create_user(username="instructor", password="secret123")

        Profile.objects.create(user=self.mohamed, role="student")
        Profile.objects.create(user=self.ahmed, role="student")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.course = Course.objects.create(
            name="Course 101",
            description="Course description",
            instructor=self.instructor,
        )

        self.mohamed_task = Task.objects.create(
            owner=self.mohamed,
            course=self.course,
            title="Mohamed task",
            description="Owned by Mohamed",
            due_date=None,
            status="pending",
        )

    def test_student_cannot_access_other_users_task_edit_route(self):
        self.client.login(username="ahmed", password="secret123")

        response = self.client.get(reverse("task_update", args=[self.mohamed_task.pk]))

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_access_other_users_task_api(self):
        self.client.force_login(self.ahmed)
        response = self.client.get(reverse("task_detail_api", args=[self.mohamed_task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_course_instructor_can_read_related_tasks_but_cannot_modify_them(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("task_api"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

        response = self.client.patch(
            reverse("task_detail_api", args=[self.mohamed_task.pk]),
            data={"title": "Changed"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
