import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.orders.models import Order, PaymentMethod, PaymentStatus
from apps.payment.models import PaymentTransaction
from apps.stores.models import Store


@pytest.fixture
def bank_transfer_order():
    store = Store.objects.create(name="TeaBerry Test", code="TB-TEST")
    return Order.objects.create(
        store=store,
        customer_name="Test Customer",
        customer_phone="0900000000",
        shipping_address="Test address",
        subtotal=100_000,
        total=100_000,
        payment_method=PaymentMethod.BANK_TRANSFER,
        payment_status=PaymentStatus.PENDING,
    )


@pytest.mark.django_db
def test_bank_transfer_page_creates_payment(
    client,
    bank_transfer_order,
    settings,
):
    settings.TEABERRY_BANK_CODE = "970436"
    settings.TEABERRY_BANK_NAME = "Test Bank"
    settings.TEABERRY_BANK_ACCOUNT = "123456789"
    settings.TEABERRY_BANK_HOLDER = "TEABERRY"

    session = client.session
    session["recent_order_ids"] = [str(bank_transfer_order.id)]
    session.save()

    response = client.get(
        reverse(
            "payment:bank-transfer",
            kwargs={"order_id": bank_transfer_order.id},
        )
    )

    assert response.status_code == 200
    assert PaymentTransaction.objects.filter(
        order=bank_transfer_order,
        amount=bank_transfer_order.total,
    ).exists()


@pytest.mark.django_db
def test_staff_order_detail_includes_payment(
    client,
    bank_transfer_order,
):
    payment = PaymentTransaction.objects.create(
        order=bank_transfer_order,
        amount=bank_transfer_order.total,
        transfer_content=bank_transfer_order.order_code,
    )
    staff = get_user_model().objects.create_user(
        email="staff@example.com",
        password="test-password",
        is_staff=True,
    )
    client.force_login(staff)

    response = client.get(
        reverse(
            "orders:staff-detail",
            kwargs={"order_id": bank_transfer_order.id},
        )
    )

    assert response.status_code == 200
    assert response.context["payment"] == payment
