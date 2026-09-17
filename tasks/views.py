import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Prefetch
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from accounts.decorators import role_required
from notifications.models import TaskNotification
from .forms import StudentNoteForm, TaskForm, TaskSubmissionForm
from .models import StudentNote, Task, TaskSubmission


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


def _can_modify(user, task):
    if user.is_superuser:
        return True
    role = _role(user)
    return role == "admin" or task.owner_id == user.id


def _visible_tasks(user):
    role = _role(user)
    if role == "student":
        today = timezone.localdate()
        return Task.objects.filter(
            course__students=user,
        ).filter(
            Q(due_date__isnull=True) | Q(due_date__gte=today),
        ).select_related("course").prefetch_related(
            Prefetch("submissions", queryset=TaskSubmission.objects.filter(student=user), to_attr="student_submissions")
        )
    if role == "instructor":
        return Task.objects.filter(Q(owner=user) | Q(course__instructor=user))
    if role == "admin":
        return Task.objects.all()
    return Task.objects.none()


def _notify_expired_tasks(user):
    today = timezone.localdate()
    expired_tasks = Task.objects.filter(
        course__students=user,
        due_date__lt=today,
    ).exclude(
        submissions__student=user,
    ).distinct()
    for task in expired_tasks:
        message = f"The deadline for task '{task.title}' has passed."
        TaskNotification.objects.get_or_create(
            recipient=user,
            task=task,
            message=message,
            defaults={"target_url": reverse("task_list")},
        )


def _task_data(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "owner": task.owner_id,
        "assigned_to": task.assigned_to_id,
        "course": task.course_id,
        "created_at": task.created_at.isoformat(),
    }


def _task_form_data(task, payload):
    data = {
        "course": task.course_id,
        "assigned_to": task.assigned_to_id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else "",
        "status": task.status,
        "priority": task.priority,
    }
    data.update(payload)
    return data


@login_required
def task_list(request):
    if _role(request.user) == "student":
        _notify_expired_tasks(request.user)
    tasks = list(_visible_tasks(request.user))
    notes = StudentNote.objects.none()
    note_form = None
    if _role(request.user) == "student":
        notes = StudentNote.objects.filter(student=request.user)
        note_form = StudentNoteForm()
        due_soon = [task for task in tasks if task.due_date and timezone.localdate() <= task.due_date <= timezone.localdate() + timedelta(days=1)]
        for task in due_soon:
            message = f"Task '{task.title}' is due in less than 24 hours!"
            TaskNotification.objects.get_or_create(
                recipient=request.user,
                task=task,
                message=message,
                defaults={"target_url": reverse("task_list")},
            )
    for task in tasks:
        task.submission_form = TaskSubmissionForm()
    return render(request, "tasks/task_list.html", {"tasks": tasks, "notes": notes, "note_form": note_form})


@role_required("student")
@require_http_methods(["POST"])
def note_create(request):
    form = StudentNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.student = request.user
        note.save()
    return redirect("task_list")


@role_required("student")
@require_http_methods(["POST"])
def note_toggle(request, note_id):
    note = StudentNote.objects.filter(id=note_id, student=request.user).first()
    if note is None:
        raise Http404
    note.is_completed = not note.is_completed
    note.save(update_fields=["is_completed"])
    return redirect("task_list")


@role_required("student")
@require_http_methods(["POST"])
def note_delete(request, note_id):
    note = StudentNote.objects.filter(id=note_id, student=request.user).first()
    if note is None:
        raise Http404
    note.delete()
    return redirect("task_list")


@role_required("student")
@require_http_methods(["POST"])
def task_submit(request, task_id):
    task = Task.objects.filter(
        id=task_id,
        course__students=request.user,
    ).filter(
        Q(due_date__isnull=True) | Q(due_date__gte=timezone.localdate()),
    ).select_related("course", "course__instructor").first()
    if task is None:
        raise Http404
    if TaskSubmission.objects.filter(task=task, student=request.user).exists():
        return redirect("task_list")

    form = TaskSubmissionForm(request.POST, request.FILES)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.task = task
        submission.student = request.user
        submission.save()
        TaskNotification.objects.create(
            recipient=task.course.instructor,
            task=task,
            target_url=reverse("task_submission_review", args=[task.id]),
            message=f"Student {request.user.username} submitted Task '{task.title}' for {task.course.name}.",
        )
        return redirect("task_list")
    tasks = list(_visible_tasks(request.user))
    for listed_task in tasks:
        listed_task.submission_form = form if listed_task.id == task.id else TaskSubmissionForm()
    return render(
        request,
        "tasks/task_list.html",
        {
            "tasks": tasks,
            "notes": StudentNote.objects.filter(student=request.user),
            "note_form": StudentNoteForm(),
        },
    )


@role_required("instructor", "admin")
def task_submission_review(request, task_id):
    task = Task.objects.filter(id=task_id, course__isnull=False).select_related("course").first()
    if task is None or (_role(request.user) != "admin" and task.course.instructor_id != request.user.id):
        raise Http404
    submissions = task.submissions.select_related("student").all()
    return render(request, "tasks/task_submission_review.html", {"task": task, "submissions": submissions})


@role_required("instructor", "admin")
def task_create(request):
    form = TaskForm(request.POST or None, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Add Task"})


@role_required("student", "instructor", "admin")
def task_update(request, task_id):
    task = _visible_tasks(request.user).filter(id=task_id).first()
    if task is None:
        raise Http404

    if task.owner_id != request.user.id and _role(request.user) != "admin":
        raise Http404

    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@role_required("student", "instructor", "admin")
def task_delete(request, task_id):
    task = _visible_tasks(request.user).filter(id=task_id).first()
    if task is None:
        raise Http404

    if task.owner_id != request.user.id and _role(request.user) != "admin":
        raise Http404

    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@role_required("student")
@require_http_methods(["POST"])
def task_complete(request, task_id):
    task = Task.objects.filter(Q(owner=request.user) | Q(assigned_to=request.user)).filter(id=task_id).first()
    if task is None:
        raise Http404
    task.status = "completed"
    task.save()
    return redirect("task_list")


@login_required
@require_http_methods(["GET", "POST"])
def task_api(request):
    if request.method == "GET":
        return JsonResponse({"results": [_task_data(task) for task in _visible_tasks(request.user)]})

    if _role(request.user) not in {"instructor", "admin"}:
        return JsonResponse({"detail": "Only instructors and admins can create course tasks."}, status=403)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)
    form = TaskForm(payload, user=request.user)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    task = form.save(commit=False)
    task.owner = request.user
    task.save()
    return JsonResponse(_task_data(task), status=201)


@login_required
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def task_detail_api(request, task_id):
    task = _visible_tasks(request.user).filter(id=task_id).first()
    if task is None:
        raise Http404
    if request.method == "GET":
        return JsonResponse(_task_data(task))

    student_assigned = _role(request.user) == "student" and task.assigned_to_id == request.user.id
    if not _can_modify(request.user, task) and not student_assigned:
        return JsonResponse({"detail": "You do not have permission to modify this task."}, status=403)

    if request.method == "DELETE":
        if not _can_modify(request.user, task):
            return JsonResponse({"detail": "You do not have permission to modify this task."}, status=403)
        task.delete()
        return JsonResponse(status=204)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)

    if _role(request.user) == "student" and task.owner_id != request.user.id:
        task.status = "completed"
        task.save()
        return JsonResponse(_task_data(task))

    form_data = _task_form_data(task, payload) if request.method == "PATCH" else payload
    form = TaskForm(form_data, instance=task, user=request.user)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    task = form.save()
    return JsonResponse(_task_data(task))
