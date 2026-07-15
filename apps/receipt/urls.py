from django.urls import path

from . import views

app_name = "receipt"

urlpatterns = [
    path(
        "<uuid:order_id>/",
        views.receipt_detail_view,
        name="detail",
    ),
]
