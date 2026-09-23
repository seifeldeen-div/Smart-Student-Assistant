import json
import logging
import traceback

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from courses.models import Course
from tasks.models import Task

from .agent import FALLBACK_REPLY, format_tool_result, run_agent
from .models import ChatMessage
from .tools import delete_task

logger = logging.getLogger(__name__)


def _get_gemini_client():
    from google import genai

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _build_user_context(user):
    # Build this context from the database for every request; never reuse chat/session task data.
    active_tasks = Task.objects.filter(
        course__students=user,
    ).filter(
        Q(due_date__isnull=True) | Q(due_date__gte=timezone.localdate()),
    ).select_related("course").distinct()
    courses = Course.objects.filter(students=user)
    taught_courses = Course.objects.filter(instructor=user)
    role = "admin" if user.is_superuser else getattr(getattr(user, "profile", None), "role", None)

    task_data = [
        {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "course": task.course.name if task.course else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "status": task.get_status_display(),
            "priority": task.get_priority_display(),
        }
        for task in active_tasks
    ]
    course_data = [
        {"name": course.name, "description": course.description}
        for course in courses
    ]
    taught_data = [
        {"id": course.id, "name": course.name, "description": course.description}
        for course in taught_courses
    ]

    return json.dumps(
        {"role": role, "tasks": task_data, "enrolled_courses": course_data, "taught_courses": taught_data},
        ensure_ascii=True,
        indent=2,
    )


@login_required
def chat_view(request):
    try:
        history = ChatMessage.objects.filter(user=request.user).order_by("created_at")

        if request.method == "GET":
            return render(request, "chat/chat.html", {"history": history})

        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed."}, status=405)

        if request.content_type == "application/json":
            try:
                payload = json.loads(request.body or "{}")
            except (TypeError, ValueError):
                return JsonResponse({"error": "Invalid JSON body."}, status=400)
            user_message = str(payload.get("user_message", "")).strip()
        else:
            user_message = request.POST.get("user_message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Please enter a message."}, status=400)

        request.session.pop("chat_context", None)
        request.session.pop("task_context", None)
        user_context = _build_user_context(request.user)
        pending_delete = request.session.get("pending_delete")
        if pending_delete is not None:
            if user_message.casefold() in {"yes", "y", "confirm", "confirm delete"}:
                result = delete_task(request.user, pending_delete, confirmed=True)
                request.session.pop("pending_delete", None)
                assistant_reply = format_tool_result(
                    _get_gemini_client(),
                    "delete_task",
                    result,
                )
            else:
                request.session.pop("pending_delete", None)
                assistant_reply = "Deletion cancelled."
        else:
            result = run_agent(
                request.user,
                user_message,
                user_context,
            )
            if result["pending_delete"] is not None:
                request.session["pending_delete"] = result["pending_delete"]
            assistant_reply = result["reply"]
        ChatMessage.objects.create(user=request.user, role="user", content=user_message)
        ChatMessage.objects.create(
            user=request.user,
            role="assistant",
            content=assistant_reply,
        )
        return JsonResponse({"reply": assistant_reply})
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        traceback.print_exc()
        logger.exception(e)
        return JsonResponse({"reply": FALLBACK_REPLY}, status=503)
