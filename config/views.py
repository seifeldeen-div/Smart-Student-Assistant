from django.conf import settings
from django.db.models import Avg
from django.shortcuts import render

from courses.models import AcademicTopic


def home(request):
    weak_topics = AcademicTopic.objects.none()
    if request.user.is_authenticated and getattr(getattr(request.user, "profile", None), "role", None) == "student":
        weak_topics = AcademicTopic.objects.filter(
            quizzes__submissions__student=request.user,
        ).annotate(
            average_accuracy=Avg("quizzes__submissions__score"),
        ).filter(
            average_accuracy__lt=settings.WEAK_TOPIC_ACCURACY_THRESHOLD,
        )

    return render(
        request,
        "home.html",
        {
            "weak_topics": weak_topics,
            "weak_topic_threshold": settings.WEAK_TOPIC_ACCURACY_THRESHOLD,
        },
    )
