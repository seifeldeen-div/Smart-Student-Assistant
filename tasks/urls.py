from django.urls import path
from .views import note_create, note_delete, note_toggle, task_api, task_complete, task_create, task_delete, task_detail_api, task_list, task_submit, task_submission_review, task_update

urlpatterns = [
    path("api/", task_api, name="task_api"),
    path("api/<int:task_id>/", task_detail_api, name="task_detail_api"),
    path("", task_list, name="task_list"),
    path("notes/add/", note_create, name="note_create"),
    path("notes/<int:note_id>/toggle/", note_toggle, name="note_toggle"),
    path("notes/<int:note_id>/delete/", note_delete, name="note_delete"),
    path("<int:task_id>/submit/", task_submit, name="task_submit"),
    path("<int:task_id>/submissions/", task_submission_review, name="task_submission_review"),
    path("new/", task_create, name="task_create"),
    path("<int:task_id>/edit/", task_update, name="task_update"),
    path("<int:task_id>/delete/", task_delete, name="task_delete"),
    path("<int:task_id>/complete/", task_complete, name="task_complete"),
]
