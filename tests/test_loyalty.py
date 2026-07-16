import pytest

from apps.loyalty.models import (
    LoyaltyAccount,
    LoyaltyTier,
    LoyaltyTransaction,
    LoyaltyTransactionType,
)
from apps.loyalty.services import (
    LoyaltyError,
    calculate_loyalty_points,
    redeem_points,
    update_tier,
)


@pytest.mark.parametrize(
    ("amount", "expected_points"),
    [
        (150_000, 15),
        (299_000, 29),
        (9_999, 0),
    ],
)
def test_calculate_loyalty_points(
    amount,
    expected_points,
):
    assert calculate_loyalty_points(amount) == expected_points


@pytest.mark.django_db
def test_loyalty_account_and_transaction(django_user_model):
    customer = django_user_model.objects.create_user(
        email="loyalty@example.com",
        password="test-password",
    )
    account = LoyaltyAccount.objects.create(
        customer=customer,
        available_points=15,
        lifetime_points=15,
    )
    transaction = LoyaltyTransaction.objects.create(
        account=account,
        transaction_type=LoyaltyTransactionType.EARN,
        points=15,
        balance_after=15,
        note="Tích điểm đơn hàng",
    )

    assert str(account) == f"{customer.email} - 15 điểm"
    assert transaction.points == 15


@pytest.mark.django_db
def test_redeem_points_returns_discount(django_user_model):
    customer = django_user_model.objects.create_user(
        email="redeem-loyalty@example.com",
        password="test-password",
    )
    account = LoyaltyAccount.objects.create(
        customer=customer,
        available_points=380,
        lifetime_points=1_750,
    )

    discount = redeem_points(customer=customer, points=100)
    account.refresh_from_db()

    assert discount == 10_000
    assert account.available_points == 280
    assert account.transactions.get().points == -100


@pytest.mark.django_db
def test_redeem_points_rejects_insufficient_balance(django_user_model):
    customer = django_user_model.objects.create_user(
        email="low-points@example.com",
        password="test-password",
    )
    LoyaltyAccount.objects.create(customer=customer, available_points=50)

    with pytest.raises(LoyaltyError):
        redeem_points(customer=customer, points=100)


@pytest.mark.django_db
def test_update_tier_uses_lifetime_points(django_user_model):
    customer = django_user_model.objects.create_user(
        email="gold@example.com",
        password="test-password",
    )
    account = LoyaltyAccount.objects.create(
        customer=customer,
        lifetime_points=1_800,
    )

    update_tier(account)
    account.refresh_from_db()

    assert account.tier == LoyaltyTier.GOLD


@pytest.mark.django_db
def test_completing_order_earns_points(django_user_model):
    from apps.orders.models import (
        FulfillmentType,
        Order,
        OrderSource,
        OrderStatus,
        PaymentMethod,
        PaymentStatus,
    )
    from apps.orders.services import change_order_status
    from apps.stores.models import Store

    customer = django_user_model.objects.create_user(
        email="completed-order@example.com",
        password="test-password",
    )
    staff = django_user_model.objects.create_user(
        email="loyalty-staff@example.com",
        password="test-password",
        is_staff=True,
    )
    store = Store.objects.create(
        name="TeaBerry Loyalty",
        code="TB-LOYALTY",
        is_active=True,
    )
    order = Order.objects.create(
        customer=customer,
        store=store,
        source=OrderSource.ONLINE,
        fulfillment_type=FulfillmentType.DELIVERY,
        customer_name="Loyal Customer",
        customer_phone="0900000001",
        customer_email=customer.email,
        shipping_address="Test address",
        subtotal=150_000,
        shipping_fee=0,
        discount=0,
        total=150_000,
        payment_method=PaymentMethod.COD,
        payment_status=PaymentStatus.PAID,
        status=OrderStatus.DELIVERING,
    )

    change_order_status(
        order_id=order.id,
        new_status=OrderStatus.COMPLETED,
        actor=staff,
    )

    account = LoyaltyAccount.objects.get(customer=customer)
    assert account.available_points == 15
    assert account.lifetime_points == 15
    assert account.transactions.get(order=order).points == 15
