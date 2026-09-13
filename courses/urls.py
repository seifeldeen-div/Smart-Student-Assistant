from django.urls import path
from .views import course_create, course_delete, course_enroll, course_list, course_update

urlpatterns = [
    path("", course_list, name="course_list"),
    path("new/", course_create, name="course_create"),
    path("<int:course_id>/edit/", course_update, name="course_update"),
    path("<int:course_id>/delete/", course_delete, name="course_delete"),
    path("<int:course_id>/enroll/", course_enroll, name="course_enroll"),
]
