from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import role_required
from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if is_admin:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(owner=request.user)
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
    task = Task.objects.filter(id=task_id).first()
    if task is None:
        raise Http404

    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and task.owner != request.user:
        raise Http404

    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@role_required("student", "admin")
def task_delete(request, task_id):
    task = Task.objects.filter(id=task_id).first()
    if task is None:
        raise Http404

    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and task.owner != request.user:
        raise Http404

    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})
