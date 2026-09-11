from django.contrib import admin
from django.urls import include, path
from .views import home

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("tasks/", include("tasks.urls")),
    path("chat/", include("chat.urls")),
]
