from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Course

@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "courses/course_list.html", {"courses": courses})
