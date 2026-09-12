from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        short_content = self.content[:60]
        return f"{self.user.username} - {self.role} - {short_content}"
