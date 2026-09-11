from tasks.models import Task

def get_my_tasks(user):
    return list(Task.objects.filter(owner=user).values("id", "title", "due_date", "status"))

def add_task(user, title, description="", due_date=None):
    if not title or not title.strip():
        raise ValueError("Task title is required.")
    return Task.objects.create(
        owner=user,
        title=title.strip(),
        description=description.strip(),
        due_date=due_date,
    )

def delete_task(user, task_id, confirmed=False):
    if not confirmed:
        return {"requires_confirmation": True, "message": "Please confirm deletion."}
    task = Task.objects.filter(id=task_id, owner=user).first()
    if not task:
        raise ValueError("Task not found or not owned by this user.")
    task.delete()
    return {"deleted": True, "task_id": task_id}
