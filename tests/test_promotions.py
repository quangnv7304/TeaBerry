from datetime import timedelta

import pytest
from django.utils import timezone

from apps.promotions.models import (
    DiscountType,
    Voucher,
)
from apps.promotions.services import (
    VoucherError,
    redeem_voucher,
    validate_voucher,
)
from apps.stores.models import Store


@pytest.fixture
def promotion_store(db):
    return Store.objects.create(
        name="TeaBerry Promotions",
        code="TB-PROMO",
        is_active=True,
    )


@pytest.mark.django_db
def test_percentage_voucher_respects_maximum_discount(
    promotion_store,
):
    now = timezone.now()

    voucher = Voucher.objects.create(
        code="WELCOME20",
        name="Welcome",
        store=promotion_store,
        discount_type=DiscountType.PERCENT,
        discount_value=20,
        maximum_discount=30_000,
        minimum_order_value=100_000,
        usage_limit_per_customer=1,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        is_active=True,
    )

    result = validate_voucher(
        code=voucher.code,
        subtotal=200_000,
        store=promotion_store,
    )

    assert result.discount_amount == 30_000
    assert result.total_after_discount == 170_000


@pytest.mark.django_db
def test_voucher_rejects_order_below_minimum(
    promotion_store,
):
    now = timezone.now()

    Voucher.objects.create(
        code="MINIMUM",
        name="Minimum order",
        store=promotion_store,
        discount_type=DiscountType.FIXED,
        discount_value=20_000,
        minimum_order_value=150_000,
        usage_limit_per_customer=1,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        is_active=True,
    )

    with pytest.raises(VoucherError):
        validate_voucher(
            code="MINIMUM",
            subtotal=100_000,
            store=promotion_store,
        )


@pytest.mark.django_db
def test_redeem_voucher_increases_used_count(
    promotion_store,
):
    from apps.orders.models import (
        FulfillmentType,
        Order,
        OrderSource,
        OrderStatus,
        PaymentMethod,
        PaymentStatus,
    )

    now = timezone.now()

    voucher = Voucher.objects.create(
        code="REDEEM10",
        name="Redeem test",
        store=promotion_store,
        discount_type=DiscountType.FIXED,
        discount_value=10_000,
        minimum_order_value=0,
        usage_limit=10,
        usage_limit_per_customer=1,
        starts_at=now - timedelta(days=1),
        ends_at=now + timedelta(days=1),
        is_active=True,
    )

    order = Order.objects.create(
        store=promotion_store,
        source=OrderSource.POS,
        fulfillment_type=FulfillmentType.PICKUP,
        customer_name="Khách lẻ",
        customer_phone="0900000000",
        customer_email="",
        shipping_address="Nhận tại quầy",
        subtotal=100_000,
        shipping_fee=0,
        discount=10_000,
        voucher_code=voucher.code,
        total=90_000,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        status=OrderStatus.CONFIRMED,
    )

    redeem_voucher(
        order=order,
        voucher=voucher,
        discount_amount=10_000,
        customer_phone=order.customer_phone,
    )

    voucher.refresh_from_db()

    assert voucher.used_count == 1
    assert order.voucher_redemption.discount_amount == 10_000
