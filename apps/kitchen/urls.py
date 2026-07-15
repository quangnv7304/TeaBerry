from django.urls import path

from . import views

app_name = "kitchen"

urlpatterns = [
    path(
        "",
        views.kitchen_board_view,
        name="board",
    ),
    path(
        "api/orders/",
        views.kitchen_orders_api_view,
        name="orders-api",
    ),
    path(
        "orders/<uuid:order_id>/status/<str:new_status>/",
        views.kitchen_change_status_view,
        name="change-status",
    ),
]