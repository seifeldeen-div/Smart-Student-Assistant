from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from notifications.models import TaskNotification

from .models import Quiz


def notify_open_quiz(quiz):
    if not quiz.is_open:
        return
    message = f"Quiz '{quiz.title}' is now open for course '{quiz.course.name}'!"
    for student in quiz.course.students.all():
        TaskNotification.objects.get_or_create(
            recipient=student,
            quiz=quiz,
            message=message,
            defaults={"target_url": reverse("quiz_list")},
        )


@receiver(post_save, sender=Quiz)
def notify_students_when_quiz_opens(sender, instance, created, **kwargs):
    if created:
        notify_open_quiz(instance)
