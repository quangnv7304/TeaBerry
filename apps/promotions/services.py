from dataclasses import dataclass

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.orders.models import Order
from apps.stores.models import Store

from .models import (
    DiscountType,
    Voucher,
    VoucherRedemption,
)


class VoucherError(Exception):
    """Lỗi nghiệp vụ mã giảm giá."""


@dataclass(frozen=True)
class VoucherResult:
    voucher: Voucher
    discount_amount: int
    total_after_discount: int


def normalize_voucher_code(code: str) -> str:
    return code.strip().upper()


def calculate_discount_amount(
    *,
    voucher: Voucher,
    subtotal: int,
) -> int:
    if voucher.discount_type == DiscountType.FIXED:
        discount_amount = int(
            voucher.discount_value
        )
    else:
        discount_amount = (
            subtotal
            * int(voucher.discount_value)
            // 100
        )

        if voucher.maximum_discount is not None:
            discount_amount = min(
                discount_amount,
                int(voucher.maximum_discount),
            )

    return min(
        subtotal,
        max(0, discount_amount),
    )


def validate_voucher(
    *,
    code: str,
    subtotal: int,
    store: Store,
    customer=None,
    customer_phone: str = "",
) -> VoucherResult:
    normalized_code = normalize_voucher_code(
        code
    )

    if not normalized_code:
        raise VoucherError(
            "Vui lòng nhập mã giảm giá."
        )

    try:
        voucher = Voucher.objects.get(
            code__iexact=normalized_code,
        )
    except Voucher.DoesNotExist as exc:
        raise VoucherError(
            "Mã giảm giá không tồn tại."
        ) from exc

    now = timezone.now()

    if not voucher.is_active:
        raise VoucherError(
            "Mã giảm giá đã bị vô hiệu hóa."
        )

    if now < voucher.starts_at:
        raise VoucherError(
            "Mã giảm giá chưa bắt đầu."
        )

    if now > voucher.ends_at:
        raise VoucherError(
            "Mã giảm giá đã hết hạn."
        )

    if (
        voucher.store_id is not None
        and voucher.store_id != store.id
    ):
        raise VoucherError(
            "Mã giảm giá không áp dụng tại cửa hàng này."
        )

    if subtotal < voucher.minimum_order_value:
        raise VoucherError(
            (
                "Đơn hàng chưa đạt giá trị tối thiểu "
                f"{voucher.minimum_order_value}đ."
            )
        )

    if (
        voucher.usage_limit is not None
        and voucher.used_count
        >= voucher.usage_limit
    ):
        raise VoucherError(
            "Mã giảm giá đã hết lượt sử dụng."
        )

    customer_redemptions = (
        VoucherRedemption.objects.filter(
            voucher=voucher,
        )
    )

    if customer is not None:
        customer_redemptions = (
            customer_redemptions.filter(
                customer=customer,
            )
        )
    elif customer_phone:
        customer_redemptions = (
            customer_redemptions.filter(
                customer_phone=customer_phone,
            )
        )
    else:
        customer_redemptions = (
            VoucherRedemption.objects.none()
        )

    if (
        customer_redemptions.count()
        >= voucher.usage_limit_per_customer
    ):
        raise VoucherError(
            "Bạn đã sử dụng hết lượt của mã này."
        )

    if (
        voucher.discount_type
        == DiscountType.PERCENT
        and voucher.discount_value > 100
    ):
        raise VoucherError(
            "Giá trị phần trăm giảm không hợp lệ."
        )

    discount_amount = calculate_discount_amount(
        voucher=voucher,
        subtotal=subtotal,
    )

    if discount_amount <= 0:
        raise VoucherError(
            "Mã giảm giá không tạo ra giá trị giảm."
        )

    return VoucherResult(
        voucher=voucher,
        discount_amount=discount_amount,
        total_after_discount=max(
            0,
            subtotal - discount_amount,
        ),
    )
@transaction.atomic
def redeem_voucher(
    *,
    order: Order,
    voucher: Voucher,
    discount_amount: int,
    customer=None,
    customer_phone: str = "",
) -> VoucherRedemption:
    locked_voucher = (
        Voucher.objects
        .select_for_update()
        .get(pk=voucher.pk)
    )

    if (
        locked_voucher.usage_limit is not None
        and locked_voucher.used_count
        >= locked_voucher.usage_limit
    ):
        raise VoucherError(
            "Mã giảm giá vừa hết lượt sử dụng."
        )

    if hasattr(order, "voucher_redemption"):
        raise VoucherError(
            "Đơn hàng đã áp dụng mã giảm giá."
        )

    redemption = VoucherRedemption.objects.create(
        voucher=locked_voucher,
        order=order,
        customer=customer,
        customer_phone=customer_phone,
        discount_amount=discount_amount,
    )

    Voucher.objects.filter(
        pk=locked_voucher.pk,
    ).update(
        used_count=F("used_count") + 1,
    )

    return redemption