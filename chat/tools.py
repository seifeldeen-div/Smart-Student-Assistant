from datetime import date

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
