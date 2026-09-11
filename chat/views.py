from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .agent import run_agent
from .models import ChatMessage

@login_required
def chat_page(request):
    answer = None
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            ChatMessage.objects.create(user=request.user, role="user", content=message)
            result = run_agent(request.user, message)
            answer = result["message"]
            ChatMessage.objects.create(user=request.user, role="assistant", content=answer)
    history = ChatMessage.objects.filter(user=request.user).order_by("created_at")
    return render(request, "chat/chat.html", {"history": history, "answer": answer})
