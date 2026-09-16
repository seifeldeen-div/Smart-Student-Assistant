from django.contrib import admin

from .models import TaskNotification


@admin.register(TaskNotification)
class TaskNotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "message", "task", "is_read", "created_at")
    list_filter = ("is_read", "recipient")
    search_fields = ("message", "recipient__username")