from django.urls import path
from .views import task_api, task_create, task_delete, task_detail_api, task_list, task_update

urlpatterns = [
    path("api/", task_api, name="task_api"),
    path("api/<int:task_id>/", task_detail_api, name="task_detail_api"),
    path("", task_list, name="task_list"),
    path("new/", task_create, name="task_create"),
    path("<int:task_id>/edit/", task_update, name="task_update"),
    path("<int:task_id>/delete/", task_delete, name="task_delete"),
]
