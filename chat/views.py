import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from courses.models import Course
from tasks.models import Task

from .agent import format_tool_result, run_agent
from .models import ChatMessage
from .tools import delete_task


def _build_user_context(user):
    tasks = Task.objects.filter(owner=user).select_related("course")
    courses = Course.objects.filter(students=user)

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
        for task in tasks
    ]
    course_data = [
        {"name": course.name, "description": course.description}
        for course in courses
    ]

    return json.dumps(
        {"tasks": task_data, "enrolled_courses": course_data},
        ensure_ascii=True,
        indent=2,
    )


def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai

    return genai.Client(api_key=api_key)


@login_required
def chat_view(request):
    history = ChatMessage.objects.filter(user=request.user).order_by("created_at")

    if request.method == "GET":
        return render(request, "chat/chat.html", {"history": history})

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    user_message = request.POST.get("user_message", "").strip()
    if not user_message:
        return JsonResponse({"error": "Please enter a message."}, status=400)

    try:
        user_context = _build_user_context(request.user)
        pending_delete = request.session.get("pending_delete")
        if pending_delete is not None:
            if user_message.casefold() in {"yes", "y", "confirm", "confirm delete"}:
                result = delete_task(request.user, pending_delete)
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
                _get_gemini_client(),
            )
            if result["pending_delete"] is not None:
                request.session["pending_delete"] = result["pending_delete"]
            assistant_reply = result["reply"]
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=503)

    ChatMessage.objects.create(user=request.user, role="user", content=user_message)
    ChatMessage.objects.create(
        user=request.user,
        role="assistant",
        content=assistant_reply,
    )
    return JsonResponse({"reply": assistant_reply})
