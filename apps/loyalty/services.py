from dataclasses import dataclass

from django.db import transaction

from apps.orders.models import Order, OrderStatus

from .models import (
    LoyaltyAccount,
    LoyaltyTier,
    LoyaltyTransaction,
    LoyaltyTransactionType,
)


class LoyaltyError(Exception):
    """Lỗi nghiệp vụ điểm thưởng."""


POINT_VALUE_IN_VND = 10_000
POINTS_TO_REDEEM_UNIT = 100
REDEEM_VALUE_PER_UNIT = 10_000
REDEEM_POINTS = POINTS_TO_REDEEM_UNIT
REDEEM_VALUE = REDEEM_VALUE_PER_UNIT


@dataclass(frozen=True)
class LoyaltyRedemptionResult:
    points_used: int
    discount_amount: int

TIER_THRESHOLDS = (
    (5_000, LoyaltyTier.PLATINUM),
    (1_500, LoyaltyTier.GOLD),
    (500, LoyaltyTier.SILVER),
    (0, LoyaltyTier.MEMBER),
)


def calculate_earned_points(*, order_total: int) -> int:
    if order_total <= 0:
        return 0
    return int(order_total) // POINT_VALUE_IN_VND


def determine_loyalty_tier(*, lifetime_points: int) -> str:
    for minimum_points, tier in TIER_THRESHOLDS:
        if lifetime_points >= minimum_points:
            return tier
    return LoyaltyTier.MEMBER


def calculate_redemption_discount(
    *,
    requested_points: int,
    available_points: int,
    payable_amount: int,
) -> LoyaltyRedemptionResult:
    if requested_points < 0:
        raise LoyaltyError("Số điểm đổi không hợp lệ.")
    if requested_points == 0:
        return LoyaltyRedemptionResult(points_used=0, discount_amount=0)
    if requested_points > available_points:
        raise LoyaltyError("Bạn không đủ điểm để đổi.")

    usable_points = (
        requested_points // POINTS_TO_REDEEM_UNIT
        * POINTS_TO_REDEEM_UNIT
    )
    if usable_points <= 0:
        raise LoyaltyError("Số điểm đổi tối thiểu là 100 điểm.")

    discount_amount = (
        usable_points // POINTS_TO_REDEEM_UNIT
        * REDEEM_VALUE_PER_UNIT
    )
    discount_amount = min(discount_amount, max(0, int(payable_amount)))
    if discount_amount <= 0:
        return LoyaltyRedemptionResult(points_used=0, discount_amount=0)

    actual_units = discount_amount // REDEEM_VALUE_PER_UNIT
    actual_points_used = actual_units * POINTS_TO_REDEEM_UNIT
    return LoyaltyRedemptionResult(
        points_used=actual_points_used,
        discount_amount=actual_units * REDEEM_VALUE_PER_UNIT,
    )


@transaction.atomic
def earn_points_for_order(*, order_id, actor=None) -> LoyaltyTransaction | None:
    try:
        order = (
            Order.objects.select_for_update()
            .select_related("customer")
            .get(pk=order_id)
        )
    except Order.DoesNotExist as exc:
        raise LoyaltyError("Không tìm thấy đơn hàng.") from exc

    if order.status != OrderStatus.COMPLETED:
        raise LoyaltyError("Chỉ cộng điểm cho đơn đã hoàn thành.")
    if order.customer_id is None:
        return None

    earned_points = calculate_earned_points(order_total=order.total)
    if earned_points <= 0:
        return None

    account, _ = LoyaltyAccount.objects.get_or_create(customer=order.customer)
    account = LoyaltyAccount.objects.select_for_update().get(pk=account.pk)
    if not account.is_active:
        return None

    existing_transaction = LoyaltyTransaction.objects.filter(
        account=account,
        order=order,
        transaction_type=LoyaltyTransactionType.EARN,
    ).first()
    if existing_transaction is not None:
        return existing_transaction

    account.available_points += earned_points
    account.lifetime_points += earned_points
    account.tier = determine_loyalty_tier(
        lifetime_points=account.lifetime_points,
    )
    account.save(update_fields=[
        "available_points", "lifetime_points", "tier", "updated_at",
    ])

    return LoyaltyTransaction.objects.create(
        account=account,
        order=order,
        transaction_type=LoyaltyTransactionType.EARN,
        points=earned_points,
        balance_after=account.available_points,
        note=f"Tích điểm từ đơn {order.order_code}",
        created_by=actor,
    )


@transaction.atomic
def redeem_points_for_order(
    *,
    order: Order,
    customer,
    requested_points: int,
    payable_amount: int,
    actor=None,
) -> LoyaltyRedemptionResult:
    if customer is None:
        raise LoyaltyError("Khách cần đăng nhập để đổi điểm.")

    try:
        account = LoyaltyAccount.objects.select_for_update().get(
            customer=customer,
            is_active=True,
        )
    except LoyaltyAccount.DoesNotExist as exc:
        raise LoyaltyError("Bạn chưa có tài khoản điểm thưởng.") from exc

    existing_transaction = LoyaltyTransaction.objects.filter(
        account=account,
        order=order,
        transaction_type=LoyaltyTransactionType.REDEEM,
    ).first()
    if existing_transaction is not None:
        points_used = abs(existing_transaction.points)
        return LoyaltyRedemptionResult(
            points_used=points_used,
            discount_amount=(
                points_used // POINTS_TO_REDEEM_UNIT
                * REDEEM_VALUE_PER_UNIT
            ),
        )

    result = calculate_redemption_discount(
        requested_points=requested_points,
        available_points=account.available_points,
        payable_amount=payable_amount,
    )
    if result.points_used == 0:
        return result

    account.available_points -= result.points_used
    account.save(update_fields=["available_points", "updated_at"])
    LoyaltyTransaction.objects.create(
        account=account,
        order=order,
        transaction_type=LoyaltyTransactionType.REDEEM,
        points=-result.points_used,
        balance_after=account.available_points,
        note=f"Đổi điểm cho đơn {order.order_code}",
        created_by=actor,
    )
    return result


@transaction.atomic
def redeem_points(*, customer, points: int, note="Đổi voucher", order=None, actor=None) -> int:
    points = int(points)
    if points <= 0 or points % REDEEM_POINTS != 0:
        raise LoyaltyError("Số điểm đổi phải là bội số của 100.")
    try:
        account = LoyaltyAccount.objects.select_for_update().get(customer=customer)
    except LoyaltyAccount.DoesNotExist as exc:
        raise LoyaltyError("Khách hàng chưa có tài khoản điểm thưởng.") from exc
    if not account.is_active:
        raise LoyaltyError("Tài khoản điểm thưởng đang bị khóa.")
    if account.available_points < points:
        raise LoyaltyError("Điểm thưởng không đủ để đổi.")

    account.available_points -= points
    account.save(update_fields=["available_points", "updated_at"])
    LoyaltyTransaction.objects.create(
        account=account,
        order=order,
        transaction_type=LoyaltyTransactionType.REDEEM,
        points=-points,
        balance_after=account.available_points,
        note=note,
        created_by=actor,
    )
    return points // REDEEM_POINTS * REDEEM_VALUE


# Compatibility aliases for existing callers.
def calculate_loyalty_points(amount: int) -> int:
    return calculate_earned_points(order_total=amount)


def update_tier(account: LoyaltyAccount) -> str:
    account.tier = determine_loyalty_tier(lifetime_points=account.lifetime_points)
    account.save(update_fields=["tier", "updated_at"])
    return account.tier
