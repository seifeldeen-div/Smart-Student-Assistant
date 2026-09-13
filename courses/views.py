from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from accounts.decorators import role_required
from .forms import CourseForm
from .models import Course


@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, "courses/course_list.html", {"courses": courses})


@role_required("instructor")
def course_create(request):
    form = CourseForm(request.POST or None)
    if form.is_valid():
        course = form.save(commit=False)
        course.instructor = request.user
        course.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Add Course"})


@role_required("instructor")
def course_update(request, course_id):
    course = Course.objects.filter(id=course_id, instructor=request.user).first()
    if course is None:
        raise Http404

    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@role_required("instructor")
def course_delete(request, course_id):
    course = Course.objects.filter(id=course_id, instructor=request.user).first()
    if course is None:
        raise Http404

    if request.method == "POST":
        course.delete()
        return redirect("course_list")
    return render(request, "courses/course_confirm_delete.html", {"course": course})


@login_required
@role_required("student")
def course_enroll(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None:
        raise Http404

    course.students.add(request.user)
    return redirect("course_list")
