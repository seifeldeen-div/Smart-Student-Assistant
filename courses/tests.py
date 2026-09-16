from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from courses.models import Course


class CourseCrudUITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="instructor", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

    def test_instructor_can_create_course_from_ui_and_list_it(self):
        self.client.login(username="instructor", password="secret123")

        response = self.client.post(
            reverse("course_create"),
            {"name": "Database Basics", "description": "Learn how tables work."},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("course_list"))
        self.assertTrue(Course.objects.filter(name="Database Basics", instructor=self.instructor).exists())

        list_response = self.client.get(reverse("course_list"))
        self.assertContains(list_response, "Database Basics")


class CourseApiPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="instructor", password="secret123")
        self.other_instructor = User.objects.create_user(username="other", password="secret123")
        self.student = User.objects.create_user(username="student", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")
        Profile.objects.create(user=self.other_instructor, role="instructor")
        Profile.objects.create(user=self.student, role="student")
        self.course = Course.objects.create(name="Private course", instructor=self.instructor)
        self.other_course = Course.objects.create(name="Other course", instructor=self.other_instructor)

    def test_student_sees_all_courses_but_cannot_modify(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("course_api"))
        self.assertEqual(len(response.json()["results"]), 2)

        detail = self.client.get(reverse("course_detail_api", args=[self.course.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], self.course.pk)

        modify = self.client.put(
            reverse("course_detail_api", args=[self.course.pk]),
            data='{"name": "Hacked"}',
            content_type="application/json",
        )
        self.assertEqual(modify.status_code, 403)

    def test_instructor_cannot_access_another_instructors_course(self):
        self.client.force_login(self.instructor)
        response = self.client.get(reverse("course_detail_api", args=[self.other_course.pk]))
        self.assertEqual(response.status_code, 404)
