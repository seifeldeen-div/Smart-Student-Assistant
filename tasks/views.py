from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import role_required
from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    if request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin":
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(owner=request.user)
    return render(request, "tasks/task_list.html", {"tasks": tasks})


@role_required("student", "admin")
def task_create(request):
    form = TaskForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Add Task"})


@role_required("student", "admin")
def task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not request.user.is_superuser and getattr(getattr(request.user, "profile", None), "role", None) != "admin" and task.owner != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@role_required("student", "admin")
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if not request.user.is_superuser and getattr(getattr(request.user, "profile", None), "role", None) != "admin" and task.owner != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})
