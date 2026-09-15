import json
import os

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from courses.models import Course
from tasks.models import Task

from .models import ChatMessage


def _build_user_context(user):
    tasks = Task.objects.filter(owner=user).select_related("course")
    courses = Course.objects.filter(students=user)

    task_data = [
        {
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


def _generate_reply(user_message, user_context):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    from google import genai

    prompt = f"""You are a read-only student assistant.
Answer the user's question using only the database context below.
Do not guess, invent, or infer facts that are not present in the context.
If the answer is not in the context, say that it is not available.
Never create, update, or delete anything.

DATABASE CONTEXT FOR THIS USER:
{user_context}

USER QUESTION:
{user_message}
"""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
       model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text.strip()


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
        assistant_reply = _generate_reply(user_message, user_context)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=503)

    ChatMessage.objects.create(user=request.user, role="user", content=user_message)
    ChatMessage.objects.create(
        user=request.user,
        role="assistant",
        content=assistant_reply,
    )
    return JsonResponse({"reply": assistant_reply})
