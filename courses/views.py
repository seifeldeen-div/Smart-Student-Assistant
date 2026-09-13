from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import role_required
from .forms import CourseForm
from .models import Course


@login_required
def course_list(request):
    courses = Course.objects.all()
    enrolled = Course.objects.filter(students=request.user)
    return render(request, "courses/course_list.html", {"courses": courses, "enrolled": enrolled})


@login_required
def course_students(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        raise Http404

    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and course.instructor != request.user:
        raise Http404

    students = course.students.all()
    return render(request, "courses/course_students.html", {"course": course, "students": students})


@role_required("instructor", "admin")
def course_create(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Add Course"})


@role_required("instructor", "admin")
def course_update(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        raise Http404

    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and course.instructor != request.user:
        raise Http404

    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@role_required("instructor", "admin")
def course_delete(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        raise Http404

    is_admin = request.user.is_superuser or getattr(getattr(request.user, "profile", None), "role", None) == "admin"
    if not is_admin and course.instructor != request.user:
        raise Http404

    if request.method == "POST":
        course.delete()
        return redirect("course_list")
    return render(request, "courses/course_confirm_delete.html", {"course": course})


@login_required
@role_required("student", "admin")
def course_enroll(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        raise Http404

    if not course.students.filter(id=request.user.id).exists():
        course.students.add(request.user)

    return redirect("course_list")
