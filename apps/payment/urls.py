from django.urls import path

from . import views

app_name = "payment"

urlpatterns = [
    path(
        "orders/<uuid:order_id>/bank-transfer/",
        views.bank_transfer_view,
        name="bank-transfer",
    ),
    path(
        "<uuid:payment_id>/submitted/",
        views.customer_submitted_view,
        name="customer-submitted",
    ),
    path(
        "<uuid:payment_id>/confirm/",
        views.staff_confirm_payment_view,
        name="staff-confirm",
    ),
]
