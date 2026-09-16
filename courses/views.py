import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, render
from accounts.decorators import role_required
from .forms import CourseForm
from .models import Course


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


def _visible_courses(user):
    role = _role(user)
    if role in {"student", "admin"}:
        return Course.objects.all()
    if role == "instructor":
        return Course.objects.filter(instructor=user)
    return Course.objects.none()


def _course_data(course):
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "schedule": course.schedule,
        "instructor": course.instructor_id,
        "students": list(course.students.values_list("id", flat=True)),
    }


def _course_form_data(course, payload):
    data = {
        "name": course.name,
        "description": course.description,
        "schedule": course.schedule,
    }
    data.update(payload)
    return data


@login_required
def course_list(request):
    courses = _visible_courses(request.user)
    enrolled = courses.filter(students=request.user)
    return render(request, "courses/course_list.html", {"courses": courses, "enrolled": enrolled})


@login_required
def course_students(request, course_id):
    course = _visible_courses(request.user).filter(id=course_id).first()
    if course is None:
        raise Http404

    if _role(request.user) not in {"instructor", "admin"}:
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
    course = _visible_courses(request.user).filter(id=course_id).first()
    if course is None:
        raise Http404

    form = CourseForm(request.POST or None, instance=course)
    if form.is_valid():
        form.save()
        return redirect("course_list")
    return render(request, "courses/course_form.html", {"form": form, "title": "Edit Course"})


@role_required("instructor", "admin")
def course_delete(request, course_id):
    course = _visible_courses(request.user).filter(id=course_id).first()
    if course is None:
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


@login_required
@require_http_methods(["GET", "POST"])
def course_api(request):
    if request.method == "GET":
        return JsonResponse({"results": [_course_data(course) for course in _visible_courses(request.user)]})

    if _role(request.user) not in {"instructor", "admin"}:
        return JsonResponse({"detail": "Only instructors can create courses."}, status=403)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)

    form = CourseForm(payload)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    course = form.save(commit=False)
    course.instructor = request.user
    course.save()
    return JsonResponse(_course_data(course), status=201)


@login_required
@require_http_methods(["GET", "PUT", "PATCH", "DELETE"])
def course_detail_api(request, course_id):
    course = _visible_courses(request.user).filter(id=course_id).first()
    if course is None:
        raise Http404

    if request.method == "GET":
        return JsonResponse(_course_data(course))
    if _role(request.user) == "student":
        return JsonResponse({"detail": "Students cannot modify courses."}, status=403)
    if request.method == "DELETE":
        course.delete()
        return JsonResponse(status=204)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Request body must be valid JSON."}, status=400)
    form_data = _course_form_data(course, payload) if request.method == "PATCH" else payload
    form = CourseForm(form_data, instance=course)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors}, status=400)
    course = form.save()
    return JsonResponse(_course_data(course))
