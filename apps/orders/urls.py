from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path(
        "checkout/",
        views.checkout_view,
        name="checkout",
    ),
    path(
        "track/",
        views.track_order_view,
        name="track",
    ),
    path(
        "<uuid:order_id>/success/",
        views.order_success_view,
        name="success",
    ),
    path(
        "<uuid:order_id>/bank-transfer/",
        views.bank_transfer_view,
        name="bank-transfer",
    ),

    path(
        "staff/",
        views.staff_order_list_view,
        name="staff-list",
    ),
    path(
        "staff/<uuid:order_id>/",
        views.staff_order_detail_view,
        name="staff-detail",
    ),
    path(
        "staff/<uuid:order_id>/status/<str:new_status>/",
        views.staff_change_status_view,
        name="staff-change-status",
    ),
    path(
        "my-orders/",
        views.customer_order_list_view,
        name="customer-list",
    ),
    path(
        "my-orders/<uuid:order_id>/",
        views.customer_order_detail_view,
        name="customer-detail",
    ),
]
