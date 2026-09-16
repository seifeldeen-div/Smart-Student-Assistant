from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from tasks.models import Task
from .models import TaskNotification


def _notify(task, recipient, message):
    TaskNotification.objects.create(task=task, recipient=recipient, message=message)


@receiver(pre_save, sender=Task)
def capture_previous_task_state(sender, instance, **kwargs):
    previous = None
    if instance.pk:
        previous = Task.objects.filter(pk=instance.pk).first()
    instance._prev_status = previous.status if previous else None
    instance._prev_assigned_to_id = previous.assigned_to_id if previous else None


@receiver(post_save, sender=Task)
def notify_on_assignment_and_completion(sender, instance, created, **kwargs):
    assigned_to_id = instance.assigned_to_id
    owner_id = instance.owner_id
    prev_assigned_to_id = getattr(instance, "_prev_assigned_to_id", None)

    if created and assigned_to_id:
        _notify(
            instance,
            instance.assigned_to,
            f'{instance.owner.get_username()} assigned a task to you: "{instance.title}"',
        )
    elif assigned_to_id and assigned_to_id != prev_assigned_to_id:
        _notify(
            instance,
            instance.assigned_to,
            f'{instance.owner.get_username()} assigned a task to you: "{instance.title}"',
        )

    prev_status = getattr(instance, "_prev_status", None)
    if (
        owner_id
        and assigned_to_id
        and owner_id != assigned_to_id
        and instance.status == "completed"
        and prev_status != "completed"
    ):
        _notify(
            instance,
            instance.owner,
            f'{instance.assigned_to.get_username()} completed your task "{instance.title}"',
        )