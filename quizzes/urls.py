from django.urls import path

from .views import (
    instructor_attempt_detail,
    instructor_quiz_submissions,
    quiz_attempt,
    quiz_create,
    quiz_list,
    quiz_question_create,
    quiz_question_delete,
    quiz_question_update,
    quiz_review,
    quiz_update,
)

urlpatterns = [
    path("", quiz_list, name="quiz_list"),
    path("course/<int:course_id>/new/", quiz_create, name="quiz_create"),
    path("<int:quiz_id>/edit/", quiz_update, name="quiz_update"),
    path("<int:quiz_id>/questions/new/", quiz_question_create, name="quiz_question_create"),
    path("questions/<int:question_id>/edit/", quiz_question_update, name="quiz_question_update"),
    path("questions/<int:question_id>/delete/", quiz_question_delete, name="quiz_question_delete"),
    path("<int:quiz_id>/take/", quiz_attempt, name="quiz_attempt"),
    path("attempts/<int:attempt_id>/review/", quiz_review, name="quiz_review"),
    path("<int:quiz_id>/submissions/", instructor_quiz_submissions, name="instructor_quiz_submissions"),
    path("attempts/<int:attempt_id>/", instructor_attempt_detail, name="instructor_attempt_detail"),
]