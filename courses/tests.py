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
