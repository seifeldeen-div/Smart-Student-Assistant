from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import role_required
from .forms import TaskForm
from .models import Task


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user)
    return render(request, "tasks/task_list.html", {"tasks": tasks})


@role_required("student")
def task_create(request):
    form = TaskForm(request.POST or None, user=request.user)
    if form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Add Task"})


@role_required("student")
def task_update(request, task_id):
    task = Task.objects.filter(id=task_id, owner=request.user).first()
    if task is None:
        raise Http404

    form = TaskForm(request.POST or None, instance=task, user=request.user)
    if form.is_valid():
        form.save()
        return redirect("task_list")
    return render(request, "tasks/task_form.html", {"form": form, "title": "Edit Task"})


@role_required("student")
def task_delete(request, task_id):
    task = Task.objects.filter(id=task_id, owner=request.user).first()
    if task is None:
        raise Http404

    if request.method == "POST":
        task.delete()
        return redirect("task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})
