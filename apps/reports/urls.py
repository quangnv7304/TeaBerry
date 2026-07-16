from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path(
        "",
        views.revenue_dashboard_view,
        name="revenue-dashboard",
    ),
]