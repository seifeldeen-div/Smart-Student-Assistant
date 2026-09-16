from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import TaskNotification


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    return render(request, "notifications/notification_list.html", {"notifications": notifications})


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    notification = request.user.notifications.filter(id=notification_id).first()
    if notification is None:
        raise Http404
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notification_list")