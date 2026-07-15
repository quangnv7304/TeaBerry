import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.orders.models import (
    FulfillmentType,
    Order,
    OrderSource,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from apps.stores.models import Store


@pytest.mark.django_db
def test_receipt_requires_login(client):
    response = client.get(
        reverse(
            "receipt:detail",
            kwargs={
                "order_id": "00000000-0000-0000-0000-000000000001",
            },
        )
    )

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_staff_can_view_pos_receipt(client):
    staff = User.objects.create_user(
        email="receipt-staff@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.STAFF,
        is_staff=True,
    )

    store = Store.objects.create(
        name="TeaBerry",
        code="TB-RECEIPT",
        is_active=True,
    )

    order = Order.objects.create(
        store=store,
        source=OrderSource.POS,
        fulfillment_type=FulfillmentType.PICKUP,
        cashier=staff,
        customer_name="Khách lẻ",
        customer_phone="",
        customer_email="",
        shipping_address="Nhận tại quầy",
        subtotal=50_000,
        shipping_fee=0,
        discount=0,
        total=50_000,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        status=OrderStatus.CONFIRMED,
    )

    client.force_login(staff)

    response = client.get(
        reverse(
            "receipt:detail",
            kwargs={"order_id": order.id},
        )
    )

    assert response.status_code == 200
    assert order.order_code.encode() in response.content