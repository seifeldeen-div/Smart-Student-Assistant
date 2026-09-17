from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import Profile
from courses.models import Course
from notifications.models import TaskNotification
from tasks.models import StudentNote, Task, TaskSubmission


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


class TaskAssignmentTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.instructor = User.objects.create_user(username="inst1", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.student = User.objects.create_user(username="stu1", password="secret123")
        Profile.objects.create(user=self.student, role="student")

        self.other_student = User.objects.create_user(username="stu2", password="secret123")
        Profile.objects.create(user=self.other_student, role="student")

        self.course = Course.objects.create(
            name="Web Development",
            description="Course description",
            instructor=self.instructor,
        )
        self.course.students.add(self.student)

        self.assign_url = reverse("task_create")
        self.list_url = reverse("task_list")

    def _assigned_task(self, **overrides):
        data = {
            "owner": self.instructor,
            "course": self.course,
            "assigned_to": self.student,
            "title": "HTML Assignment",
            "description": "Build a page",
            "status": "pending",
            "priority": "high",
        }
        data.update(overrides)
        return Task.objects.create(**data)

    def test_instructor_can_create_personal_task(self):
        self.client.login(username="inst1", password="secret123")
        response = self.client.post(self.assign_url, {
            "title": "Prepare tomorrow's lecture",
            "description": "Slides and notes",
            "priority": "high",
            "status": "pending",
        })
        self.assertRedirects(response, self.list_url)
        task = Task.objects.filter(owner=self.instructor).first()
        self.assertIsNotNone(task)
        self.assertIsNone(task.assigned_to)

    def test_instructor_can_assign_task_to_their_student(self):
        self.client.login(username="inst1", password="secret123")
        response = self.client.post(self.assign_url, {
            "title": "HTML Assignment",
            "description": "Build a page",
            "course": self.course.pk,
            "assigned_to": self.student.pk,
            "priority": "high",
            "status": "pending",
        })
        self.assertRedirects(response, self.list_url)
        task = Task.objects.filter(owner=self.instructor, assigned_to=self.student).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.status, "pending")

    def test_instructor_cannot_assign_task_to_unrelated_student(self):
        self.client.login(username="inst1", password="secret123")
        response = self.client.post(self.assign_url, {
            "title": "Bad assignment",
            "course": self.course.pk,
            "assigned_to": self.other_student.pk,
            "priority": "low",
            "status": "pending",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(owner=self.instructor, assigned_to=self.other_student).exists())

    def test_model_rejects_assignment_to_unrelated_student(self):
        with self.assertRaises(ValidationError):
            self._assigned_task(assigned_to=self.other_student)

    def test_instructor_can_see_assigned_tasks_and_status(self):
        self._assigned_task()
        self.client.login(username="inst1", password="secret123")
        response = self.client.get(self.list_url)
        self.assertContains(response, "HTML Assignment")
        self.assertContains(response, self.student.get_username())

    def test_student_can_see_task_assigned_to_them(self):
        self._assigned_task()
        self.client.login(username="stu1", password="secret123")
        response = self.client.get(self.list_url)
        self.assertContains(response, "HTML Assignment")

    def test_student_cannot_see_task_assigned_to_another_student(self):
        self._assigned_task()
        self.client.login(username="stu2", password="secret123")
        response = self.client.get(self.list_url)
        self.assertNotContains(response, "HTML Assignment")

    def test_student_can_mark_assigned_task_completed(self):
        task = self._assigned_task()
        self.client.login(username="stu1", password="secret123")
        response = self.client.post(reverse("task_complete", args=[task.pk]))
        self.assertRedirects(response, self.list_url)
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

    def test_student_cannot_mark_another_students_task_completed(self):
        task = self._assigned_task()
        self.client.login(username="stu2", password="secret123")
        response = self.client.post(reverse("task_complete", args=[task.pk]))
        self.assertEqual(response.status_code, 404)
        task.refresh_from_db()
        self.assertEqual(task.status, "pending")

    def test_student_cannot_assign_task_to_other_students(self):
        self.client.login(username="stu1", password="secret123")
        response = self.client.post(self.assign_url, {
            "title": "My own task",
            "assigned_to": self.other_student.pk,
            "priority": "low",
            "status": "pending",
        })
        self.assertRedirects(response, self.list_url)
        task = Task.objects.filter(owner=self.student).first()
        self.assertIsNotNone(task)
        self.assertIsNone(task.assigned_to)

    def test_student_cannot_edit_task_assigned_to_them(self):
        task = self._assigned_task()
        self.client.login(username="stu1", password="secret123")
        response = self.client.get(reverse("task_update", args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_instructor_sees_completion_status_after_student_completes(self):
        task_id = self._assigned_task().pk

        self.client.login(username="stu1", password="secret123")
        self.client.post(reverse("task_complete", args=[task_id]))
        self.client.logout()

        self.client.login(username="inst1", password="secret123")
        response = self.client.get(self.list_url)
        self.assertContains(response, "Completed")
        self.assertEqual(Task.objects.get(pk=task_id).status, "completed")


class TaskFormValidationErrorTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.instructor = User.objects.create_user(username="inst_x", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

        self.student = User.objects.create_user(username="stu_x", password="secret123")
        Profile.objects.create(user=self.student, role="student")

        self.course = Course.objects.create(
            name="Web Development",
            description="Course description",
            instructor=self.instructor,
        )
        self.course.students.add(self.student)

    def test_invalid_instructor_submission_renders_form_not_crash(self):
        self.client.login(username="inst_x", password="secret123")
        response = self.client.post(reverse("task_create"), {
            "title": "",
            "assigned_to": self.student.pk,
            "priority": "high",
            "status": "pending",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.exists())

    def test_invalid_student_submission_renders_form_not_crash(self):
        self.client.login(username="stu_x", password="secret123")
        response = self.client.post(reverse("task_create"), {
            "title": "",
            "priority": "low",
            "status": "pending",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.exists())

    def test_full_instructor_appoints_and_student_completes_flow(self):
        self.client.login(username="inst_x", password="secret123")
        response = self.client.post(reverse("task_create"), {
            "title": "HTML Assignment",
            "description": "Build a page",
            "course": self.course.pk,
            "assigned_to": self.student.pk,
            "priority": "high",
            "due_date": "2026-12-31",
            "status": "pending",
        })
        self.assertRedirects(response, reverse("task_list"))
        task = Task.objects.get(title="HTML Assignment")
        self.assertEqual(task.owner, self.instructor)
        self.assertEqual(task.assigned_to, self.student)
        self.assertEqual(task.status, "pending")

        self.client.logout()
        self.client.login(username="stu_x", password="secret123")
        response = self.client.get(reverse("task_list"))
        self.assertContains(response, "HTML Assignment")

        response = self.client.post(reverse("task_complete", args=[task.pk]))
        self.assertRedirects(response, reverse("task_list"))
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")

        self.client.logout()
        self.client.login(username="inst_x", password="secret123")
        response = self.client.get(reverse("task_list"))
        self.assertContains(response, "HTML Assignment")
        self.assertContains(response, "Completed")
        self.assertContains(response, self.student.get_username())


class InstructorPersonalTaskTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="inst_p", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")

    def test_instructor_personal_task_appears_in_own_list(self):
        self.client.login(username="inst_p", password="secret123")
        response = self.client.post(reverse("task_create"), {
            "title": "Prepare tomorrow's lecture",
            "description": "Slides and notes",
            "priority": "medium",
            "status": "pending",
        })
        self.assertRedirects(response, reverse("task_list"))
        task = Task.objects.get(owner=self.instructor)
        self.assertIsNone(task.assigned_to)

        response = self.client.get(reverse("task_list"))
        self.assertContains(response, "Prepare tomorrow's lecture", html=True)
        self.assertContains(response, "Personal")


    def test_student_does_not_see_instructor_personal_task(self):
        student = get_user_model().objects.create_user(username="stu_p", password="secret123")
        Profile.objects.create(user=student, role="student")

        self.client.login(username="inst_p", password="secret123")
        self.client.post(reverse("task_create"), {
            "title": "Prepare tomorrow's lecture",
            "priority": "medium",
            "status": "pending",
        })
        self.client.logout()

        self.client.login(username="stu_p", password="secret123")
        response = self.client.get(reverse("task_list"))
        self.assertNotContains(response, "Prepare tomorrow's lecture")


class TaskSubmissionWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="reviewer", password="secret123")
        self.student = User.objects.create_user(username="submitter", password="secret123")
        self.other_student = User.objects.create_user(username="outsider", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.other_student, role="student")
        self.course = Course.objects.create(name="Malware Analysis", instructor=self.instructor)
        self.course.students.add(self.student)
        self.task = Task.objects.create(
            owner=self.instructor,
            course=self.course,
            title="Analyze sample",
            description="Write a short report.",
            due_date=timezone.localdate() + timedelta(days=1),
        )

    def test_student_sees_only_enrolled_course_tasks_and_due_reminder(self):
        other_course = Course.objects.create(name="Private Course", instructor=self.instructor)
        Task.objects.create(owner=self.instructor, course=other_course, title="Hidden task")

        self.client.force_login(self.student)
        response = self.client.get(reverse("task_list"))

        self.assertContains(response, "Analyze sample")
        self.assertContains(response, "Malware Analysis")
        self.assertNotContains(response, "Hidden task")
        self.assertTrue(TaskNotification.objects.filter(recipient=self.student, task=self.task).exists())

    def test_student_can_submit_file_and_instructor_is_notified(self):
        self.client.force_login(self.student)
        upload = SimpleUploadedFile("report.pdf", b"report content", content_type="application/pdf")

        response = self.client.post(
            reverse("task_submit", args=[self.task.pk]),
            {"submission_file": upload, "notes": "Completed analysis."},
        )

        self.assertRedirects(response, reverse("task_list"))
        submission = TaskSubmission.objects.get(task=self.task, student=self.student)
        self.assertEqual(submission.status, "Submitted")
        notification = TaskNotification.objects.get(recipient=self.instructor, task=self.task)
        self.assertIn("submitter", notification.message)
        self.assertEqual(notification.target_url, reverse("task_submission_review", args=[self.task.pk]))

    def test_instructor_can_review_only_own_course_submissions(self):
        TaskSubmission.objects.create(task=self.task, student=self.student, submission_link="https://github.com/example/repo")
        self.client.force_login(self.instructor)

        response = self.client.get(reverse("task_submission_review", args=[self.task.pk]))

        self.assertContains(response, "submitter")
        self.assertContains(response, "github.com/example/repo")

        other_instructor = get_user_model().objects.create_user(username="other-reviewer", password="secret123")
        Profile.objects.create(user=other_instructor, role="instructor")
        self.client.force_login(other_instructor)
        self.assertEqual(self.client.get(reverse("task_submission_review", args=[self.task.pk])).status_code, 404)

    def test_unenrolled_student_cannot_submit(self):
        self.client.force_login(self.other_student)

        response = self.client.post(
            reverse("task_submit", args=[self.task.pk]),
            {"submission_link": "https://github.com/example/repo"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TaskSubmission.objects.exists())

    def test_expired_unsubmitted_task_is_not_active_and_notifies_student(self):
        expired_task = Task.objects.create(
            owner=self.instructor,
            course=self.course,
            title="Expired analysis",
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("task_list"))

        self.assertNotContains(response, "Expired analysis")
        notification = TaskNotification.objects.get(recipient=self.student, task=expired_task)
        self.assertEqual(notification.message, "The deadline for task 'Expired analysis' has passed.")
        self.assertEqual(TaskNotification.objects.filter(recipient=self.student, task=expired_task).count(), 1)

        self.client.get(reverse("task_list"))
        self.assertEqual(TaskNotification.objects.filter(recipient=self.student, task=expired_task).count(), 1)

    def test_expired_submitted_task_is_archived_but_submission_is_preserved(self):
        expired_task = Task.objects.create(
            owner=self.instructor,
            course=self.course,
            title="Submitted analysis",
            due_date=timezone.localdate() - timedelta(days=1),
        )
        submission = TaskSubmission.objects.create(
            task=expired_task,
            student=self.student,
            submission_link="https://github.com/example/submitted-analysis",
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse("task_list"))

        self.assertNotContains(response, "Submitted analysis")
        self.assertTrue(TaskSubmission.objects.filter(pk=submission.pk, task=expired_task, student=self.student).exists())
        self.assertFalse(TaskNotification.objects.filter(recipient=self.student, task=expired_task).exists())

    def test_student_cannot_submit_after_task_deadline(self):
        expired_task = Task.objects.create(
            owner=self.instructor,
            course=self.course,
            title="Late analysis",
            due_date=timezone.localdate() - timedelta(days=1),
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("task_submit", args=[expired_task.pk]),
            {"submission_link": "https://github.com/example/late-analysis"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(TaskSubmission.objects.filter(task=expired_task, student=self.student).exists())


class StudentNotesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(username="notes-student", password="secret123")
        self.other_student = User.objects.create_user(username="other-notes-student", password="secret123")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.other_student, role="student")

    def test_student_can_add_toggle_and_delete_own_note(self):
        self.client.force_login(self.student)

        response = self.client.post(reverse("note_create"), {"content": "Review SQL joins"})
        self.assertRedirects(response, reverse("task_list"))
        note = StudentNote.objects.get(student=self.student)

        self.client.post(reverse("note_toggle", args=[note.pk]))
        note.refresh_from_db()
        self.assertTrue(note.is_completed)

        self.client.post(reverse("note_delete", args=[note.pk]))
        self.assertFalse(StudentNote.objects.filter(pk=note.pk).exists())

    def test_student_cannot_modify_another_students_note(self):
        note = StudentNote.objects.create(student=self.other_student, content="Private note")
        self.client.force_login(self.student)

        self.assertEqual(self.client.post(reverse("note_toggle", args=[note.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("note_delete", args=[note.pk])).status_code, 404)
        self.assertTrue(StudentNote.objects.filter(pk=note.pk).exists())


class TaskCreationNavigationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.student = User.objects.create_user(username="nav-student", password="secret123")
        self.instructor = User.objects.create_user(username="nav-instructor", password="secret123")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.instructor, role="instructor")

    def test_student_dashboard_points_to_notes_instead_of_task_creation(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Personal Study Notes")
        self.assertNotContains(response, "/tasks/new/")

    def test_instructor_dashboard_keeps_new_task_action(self):
        self.client.force_login(self.instructor)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "New task")
        self.assertContains(response, reverse("task_create"))



  