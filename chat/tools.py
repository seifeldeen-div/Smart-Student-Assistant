from datetime import date

from django.db import transaction

from courses.forms import CourseForm
from courses.models import Course
from tasks.models import Task


def get_my_tasks(user):
    tasks = Task.objects.filter(owner=user).values(
        "id", "title", "description", "due_date", "status", "priority"
    )
    return [
        {
            **task,
            "due_date": task["due_date"].isoformat() if task["due_date"] else None,
        }
        for task in tasks
    ]


def add_task(user, title, description="", due_date=None, priority="low"):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Task title is required.")
    title = title.strip()
    if len(title) > 150:
        raise ValueError("Task title must be 150 characters or fewer.")
    if not isinstance(description, str):
        raise ValueError("Task description must be text.")
    if priority not in dict(Task.PRIORITY_CHOICES):
        raise ValueError("Task priority is invalid.")
    if due_date:
        try:
            due_date = date.fromisoformat(due_date)
        except (TypeError, ValueError) as error:
            raise ValueError("Due date must use YYYY-MM-DD format.") from error

    return Task.objects.create(
        owner=user,
        title=title,
        description=description.strip(),
        due_date=due_date,
        priority=priority,
    )


def delete_task(user, task_id):
    if isinstance(task_id, bool):
        raise ValueError("Task ID must be a positive integer.")
    try:
        task_id = int(task_id)
    except (TypeError, ValueError) as error:
        raise ValueError("Task ID must be a positive integer.") from error
    if task_id <= 0:
        raise ValueError("Task ID must be a positive integer.")

    task = Task.objects.filter(id=task_id, owner=user).first()
    if not task:
        raise ValueError("Task not found or not owned by this user.")
    task_title = task.title
    task.delete()
    return {"deleted": True, "task_id": task_id, "title": task_title}


def _user_role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


def _can_manage_courses(user):
    if user.is_superuser:
        return True
    return _user_role(user) == "instructor"


def _can_enroll(user):
    return _user_role(user) in {"student", "admin"}


def _strip_optional(value):
    return value.strip() if isinstance(value, str) else ""


def create_course(user, name, description="", schedule=""):
    role = _user_role(user) or "unknown"
    if not _can_manage_courses(user):
        return {
            "status": "permission_denied",
            "message": f"You are logged in as {role}, so you cannot create courses. Only instructors can create courses.",
        }

    if not isinstance(name, str) or not name.strip():
        return {
            "status": "missing_fields",
            "message": "What is the course name?",
            "fields": ["name"],
        }

    form = CourseForm(
        {
            "name": name.strip(),
            "description": _strip_optional(description),
            "schedule": _strip_optional(schedule),
        }
    )
    if not form.is_valid():
        return {
            "status": "validation_error",
            "message": "The course information provided is invalid.",
            "errors": form.errors,
        }

    with transaction.atomic():
        course = form.save(commit=False)
        course.instructor = user
        course.save()

    return {
        "status": "created",
        "course": {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "schedule": course.schedule,
            "instructor_id": course.instructor_id,
        },
    }


def enroll_in_course(user, course_name):
    role = _user_role(user) or "unknown"
    if not _can_enroll(user):
        if role == "instructor":
            return {
                "status": "not_allowed",
                "message": "Instructors cannot enroll in courses. Only students can enroll in courses.",
            }
        return {
            "status": "permission_denied",
            "message": "You are not allowed to enroll in courses.",
        }

    if not isinstance(course_name, str) or not course_name.strip():
        return {
            "status": "missing_fields",
            "message": "Which course would you like to enroll in?",
            "fields": ["course_name"],
        }

    course_name = course_name.strip()
    course = Course.objects.filter(name__iexact=course_name).first()
    if course is None:
        return {"status": "not_found", "message": "I couldn't find that course."}

    if course.students.filter(id=user.id).exists():
        return {
            "status": "already_enrolled",
            "message": f"You are already enrolled in {course.name}.",
        }

    course.students.add(user)
    return {
        "status": "enrolled",
        "course": {"id": course.id, "name": course.name},
    }
