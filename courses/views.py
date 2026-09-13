from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import role_required
from .forms import CourseForm
from .models import Course


@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "courses/course_list.html", {"courses": courses})


@role_required("instructor", "admin")
def course_create(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        course = form.save(commit=False)
        if not request.user.is_superuser and getattr(getattr(request.user, "profile", None), "role", None) != "admin":
            course.instructor = request.user
        course.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Add Course"})


@role_required("instructor", "admin")
def course_update(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and course.instructor != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        updated_course = form.save(commit=False)
        if not is_admin:
            updated_course.instructor = request.user
        updated_course.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@role_required("instructor", "admin")
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and course.instructor != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == "POST":
        course.delete()
        return redirect("course_list")
    return render(request, "courses/course_confirm_delete.html", {"course": course})
