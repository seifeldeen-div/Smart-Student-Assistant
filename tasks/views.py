import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from accounts.decorators import role_required
from .forms import TaskForm
from .models import Task


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


def _visible_tasks(user):
    role = _role(user)
    if role == "student":
        return Task.objects.filter(owner=user)
    if role == "instructor":
        return Task.objects.filter(course__instructor=user)
    if role == "admin":
        return Task.objects.all()
    return Task.objects.none()


def _task_data(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "owner": task.owner_id,
        "course": task.course_id,
        "created_at": task.created_at.isoformat(),
    }


def _task_form_data(task, payload):
    data = {
        "course": task.course_id,
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
    tasks = _visible_tasks(request.user)
    return render(request, "tasks/task_list.html", {"tasks": tasks})


@role_required("student", "admin")
def task_create(request):
    form = TaskForm(request.POST or None, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Add Task"})


@role_required("student", "admin")
def task_update(request, task_id):
    task = _visible_tasks(request.user).filter(id=task_id).first()
    if task is None:
        raise Http404

    if _role(request.user) not in {"student", "admin"}:
        raise Http404

    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@role_required("student", "admin")
def task_delete(request, task_id):
    task = _visible_tasks(request.user).filter(id=task_id).first()
    if task is None:
        raise Http404

    if _role(request.user) not in {"student", "admin"}:
        raise Http404

    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
@require_http_methods(["GET", "POST"])
def task_api(request):
    if request.method == "GET":
        return JsonResponse({"results": [_task_data(task) for task in _visible_tasks(request.user)]})

    if _role(request.user) not in {"student", "admin"}:
        return JsonResponse({"detail": "Only students can create tasks."}, status=403)
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
    if _role(request.user) not in {"student", "admin"}:
        return JsonResponse({"detail": "Instructors have read-only task access."}, status=403)
    if request.method == "DELETE":
        task.delete()
        return JsonResponse(status=204)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)
    form_data = _task_form_data(task, payload) if request.method == "PATCH" else payload
    form = TaskForm(form_data, instance=task, user=request.user)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    task = form.save(commit=False)
    task.owner = request.user
    task.save()
    return JsonResponse(_task_data(task))
