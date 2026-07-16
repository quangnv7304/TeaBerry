from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.orders.models import (
    OrderSource,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from apps.stores.models import Store

from .models import ShiftStatus, WorkShift


class ShiftError(Exception):
    """Lỗi nghiệp vụ ca làm việc."""


def get_open_shift(
    *,
    cashier,
    store: Store | None = None,
) -> WorkShift | None:
    queryset = WorkShift.objects.filter(
        cashier=cashier,
        status=ShiftStatus.OPEN,
    ).select_related(
        "store",
        "cashier",
    )

    if store is not None:
        queryset = queryset.filter(store=store)

    return queryset.first()


@transaction.atomic
def open_shift(
    *,
    cashier,
    store_id: int,
    opening_cash: int,
    note: str = "",
) -> WorkShift:
    if not cashier.is_authenticated:
        raise ShiftError(
            "Bạn cần đăng nhập để mở ca."
        )

    if opening_cash < 0:
        raise ShiftError(
            "Tiền đầu ca không hợp lệ."
        )

    store = (
        Store.objects
        .select_for_update()
        .get(
            pk=store_id,
            is_active=True,
        )
    )

    existing_shift = (
        WorkShift.objects
        .select_for_update()
        .filter(
            cashier=cashier,
            store=store,
            status=ShiftStatus.OPEN,
        )
        .first()
    )

    if existing_shift is not None:
        raise ShiftError(
            "Bạn đang có một ca mở tại cửa hàng này."
        )

    return WorkShift.objects.create(
        cashier=cashier,
        store=store,
        opening_cash=opening_cash,
        expected_cash=opening_cash,
        opening_note=note.strip(),
        status=ShiftStatus.OPEN,
    )


def calculate_shift_cash_sales(
    *,
    shift: WorkShift,
) -> int:
    total = (
        shift.orders
        .filter(
            source=OrderSource.POS,
            payment_method=PaymentMethod.CASH,
            payment_status=PaymentStatus.PAID,
        )
        .exclude(
            status=OrderStatus.CANCELLED,
        )
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    return int(total)


@transaction.atomic
def close_shift(
    *,
    shift_id: int,
    cashier,
    actual_cash: int,
    note: str = "",
) -> WorkShift:
    if actual_cash < 0:
        raise ShiftError(
            "Tiền mặt thực tế không hợp lệ."
        )

    try:
        shift = (
            WorkShift.objects
            .select_for_update()
            .select_related(
                "store",
                "cashier",
            )
            .get(pk=shift_id)
        )
    except WorkShift.DoesNotExist as exc:
        raise ShiftError(
            "Không tìm thấy ca làm việc."
        ) from exc

    if shift.cashier_id != cashier.id and not cashier.is_superuser:
        raise ShiftError(
            "Bạn không có quyền đóng ca này."
        )

    if shift.status != ShiftStatus.OPEN:
        raise ShiftError(
            "Ca làm việc đã được đóng."
        )

    cash_sales = calculate_shift_cash_sales(
        shift=shift,
    )

    expected_cash = (
        int(shift.opening_cash)
        + cash_sales
    )

    shift.expected_cash = expected_cash
    shift.actual_cash = actual_cash
    shift.cash_difference = (
        actual_cash - expected_cash
    )
    shift.closing_note = note.strip()
    shift.status = ShiftStatus.CLOSED
    shift.closed_at = timezone.now()

    shift.save(
        update_fields=[
            "expected_cash",
            "actual_cash",
            "cash_difference",
            "closing_note",
            "status",
            "closed_at",
        ]
    )

    return shift