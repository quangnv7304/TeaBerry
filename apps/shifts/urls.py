from django.urls import path

from . import views

app_name = "shifts"

urlpatterns = [
    path(
        "",
        views.shift_dashboard_view,
        name="dashboard",
    ),
    path(
        "open/",
        views.open_shift_view,
        name="open",
    ),
    path(
        "<int:shift_id>/close/",
        views.close_shift_view,
        name="close",
    ),
]