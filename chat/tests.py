from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Profile
from courses.models import AcademicTopic, Course, Quiz, QuizSubmission
from tasks.models import Task

from .agent import TOOL_DECLARATIONS, run_agent
from .tools import (
    create_course,
    delete_task,
    enroll_in_course,
    filter_tasks_by_priority,
    get_course_details,
    get_my_courses,
    get_my_performance,
    get_upcoming_tasks,
    get_weak_topics,
)


class AgentCourseToolsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor_a = User.objects.create_user(username="prof_a", password="secret123")
        self.instructor_b = User.objects.create_user(username="prof_b", password="secret123")
        self.student = User.objects.create_user(username="student", password="secret123")
        Profile.objects.create(user=self.instructor_a, role="instructor")
        Profile.objects.create(user=self.instructor_b, role="instructor")
        Profile.objects.create(user=self.student, role="student")

    def test_instructor_creates_course_and_it_persists(self):
        result = create_course(
            self.instructor_a,
            name="Python Programming",
            description="Introduction to Python.",
        )

        self.assertEqual(result["status"], "created")
        course = Course.objects.get(id=result["course"]["id"])
        self.assertEqual(course.name, "Python Programming")
        self.assertEqual(course.instructor_id, self.instructor_a.id)
        self.assertEqual(course.description, "Introduction to Python.")

    def test_student_cannot_create_course(self):
        result = create_course(self.student, name="Python Programming")

        self.assertEqual(result["status"], "permission_denied")
        self.assertFalse(Course.objects.filter(name="Python Programming").exists())
        self.assertIn("student", result["message"])

    def test_instructor_creates_no_incomplete_course_without_name(self):
        result = create_course(self.instructor_a, name="")

        self.assertEqual(result["status"], "missing_fields")
        self.assertEqual(Course.objects.count(), 0)

    def test_student_enrolls_in_existing_course(self):
        course = Course.objects.create(name="Python Programming", instructor=self.instructor_a)

        result = enroll_in_course(self.student, "Python Programming")

        self.assertEqual(result["status"], "enrolled")
        self.assertEqual(result["course"]["id"], course.id)
        self.assertEqual(list(course.students.all()), [self.student])

    def test_student_sees_enrolled_course_in_dashboard_query(self):
        course = Course.objects.create(name="Python Programming", instructor=self.instructor_a)
        course.students.add(self.student)

        self.assertEqual(list(Course.objects.filter(students=self.student)), [course])

    def test_student_duplicate_enrollment_is_rejected(self):
        course = Course.objects.create(name="Python Programming", instructor=self.instructor_a)
        course.students.add(self.student)

        result = enroll_in_course(self.student, "python programming")

        self.assertEqual(result["status"], "already_enrolled")
        self.assertEqual(course.students.count(), 1)

    def test_student_cannot_enroll_in_nonexistent_course(self):
        result = enroll_in_course(self.student, "Nonexistent Course")

        self.assertEqual(result["status"], "not_found")
        self.assertIn("couldn't find", result["message"])

    def test_student_cannot_create_course_even_if_claiming_instructor(self):
        result = create_course(self.student, name="Python Programming")

        self.assertEqual(result["status"], "permission_denied")
        self.assertFalse(Course.objects.filter(name="Python Programming").exists())

    def test_instructor_cannot_enroll_in_another_instructors_course(self):
        Course.objects.create(name="Python Programming", instructor=self.instructor_a)

        result = enroll_in_course(self.instructor_b, "Python Programming")

        self.assertEqual(result["status"], "not_allowed")
        self.assertEqual(
            Course.objects.filter(name="Python Programming", students=self.instructor_b).count(),
            0,
        )

    def test_course_ownership_is_always_the_authenticated_user(self):
        result = create_course(self.instructor_a, name="Python Programming")

        course = Course.objects.get(id=result["course"]["id"])
        self.assertEqual(course.instructor_id, self.instructor_a.id)

        second = create_course(self.instructor_b, name="Advanced Python")
        other = Course.objects.get(id=second["course"]["id"])
        self.assertEqual(other.instructor_id, self.instructor_b.id)
        self.assertNotEqual(other.instructor_id, course.instructor_id)

    def test_superuser_can_create_course(self):
        User = get_user_model()
        superuser = User.objects.create_superuser(username="root", password="secret123", email="root@example.com")

        result = create_course(superuser, name="Django Masterclass")

        self.assertEqual(result["status"], "created")
        self.assertTrue(Course.objects.filter(name="Django Masterclass", instructor=superuser).exists())

    def test_admin_profile_user_cannot_create_course(self):
        User = get_user_model()
        admin_user = User.objects.create_user(username="admin_user", password="secret123")
        Profile.objects.create(user=admin_user, role="admin")

        result = create_course(admin_user, name="Django Masterclass")

        self.assertEqual(result["status"], "permission_denied")
        self.assertFalse(Course.objects.filter(name="Django Masterclass").exists())


class Phase15AgentReadToolsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.instructor = User.objects.create_user(username="tools-instructor", password="secret123")
        self.student = User.objects.create_user(username="tools-student", password="secret123")
        self.other_student = User.objects.create_user(username="other-tools-student", password="secret123")
        Profile.objects.create(user=self.instructor, role="instructor")
        Profile.objects.create(user=self.student, role="student")
        Profile.objects.create(user=self.other_student, role="student")
        self.course = Course.objects.create(name="Database Systems", instructor=self.instructor)
        self.course.students.add(self.student)
        AcademicTopic.objects.create(name="SQL Joins")
        self.topic = AcademicTopic.objects.get(name="SQL Joins")
        self.quiz = Quiz.objects.create(title="Joins quiz", course=self.course, topic=self.topic)

    @override_settings(WEAK_TOPIC_ACCURACY_THRESHOLD=60)
    def test_all_read_tools_are_scoped_and_structured(self):
        Task.objects.create(
            owner=self.student,
            title="Due soon",
            priority="high",
            due_date=timezone.localdate() + timedelta(days=1),
        )
        Task.objects.create(owner=self.student, title="Low task", priority="low")
        Task.objects.create(
            owner=self.other_student,
            title="Another student's task",
            priority="high",
            due_date=timezone.localdate() + timedelta(days=1),
        )
        QuizSubmission.objects.create(student=self.student, quiz=self.quiz, score=40)
        QuizSubmission.objects.create(student=self.student, quiz=self.quiz, score=50)
        QuizSubmission.objects.create(student=self.other_student, quiz=self.quiz, score=0)

        self.assertEqual([task["title"] for task in filter_tasks_by_priority(self.student, "High")], ["Due soon"])
        self.assertEqual([task["title"] for task in get_upcoming_tasks(self.student)], ["Due soon"])
        self.assertEqual([course["name"] for course in get_my_courses(self.student)], ["Database Systems"])
        details = get_course_details(self.student, "database systems")
        self.assertEqual(details["course"]["name"], "Database Systems")
        self.assertEqual(get_my_performance(self.student)["average_score"], 45)
        self.assertEqual([topic["name"] for topic in get_weak_topics(self.student)], ["SQL Joins"])

    def test_delete_requires_explicit_confirmation(self):
        task = Task.objects.create(owner=self.student, title="Keep me", priority="low")

        result = delete_task(self.student, task.id)

        self.assertTrue(result["confirmation_required"])
        self.assertTrue(Task.objects.filter(id=task.id).exists())

    def test_llm_interface_dispatches_registered_tool(self):
        function_call = SimpleNamespace(name="get_my_courses", args={})
        first_response = SimpleNamespace(
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(function_call=function_call)]))],
            text="",
        )
        follow_up = SimpleNamespace(text="You are enrolled in Database Systems.")

        class FakeModels:
            def __init__(self):
                self.calls = []

            def generate_content(self, **kwargs):
                self.calls.append(kwargs)
                return first_response if len(self.calls) == 1 else follow_up

        client = SimpleNamespace(models=FakeModels())
        result = run_agent(self.student, "What courses am I taking?", "{}", client)

        declared_names = {declaration.name for declaration in TOOL_DECLARATIONS}
        self.assertIn("get_my_courses", declared_names)
        self.assertEqual(result["reply"], "You are enrolled in Database Systems.")
        self.assertEqual(len(client.models.calls), 2)