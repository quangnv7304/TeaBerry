from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import UserRole
from apps.pos.cart import PosCart
from apps.stores.models import Store

from .forms import CloseShiftForm, OpenShiftForm
from .models import ShiftStatus, WorkShift
from .services import (
    ShiftError,
    calculate_shift_cash_sales,
    close_shift,
    get_open_shift,
    open_shift,
)


SHIFT_ROLES = {
    UserRole.STAFF,
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_shift_access(user) -> None:
    if user.is_superuser:
        return

    if user.role not in SHIFT_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền quản lý ca."
        )


@login_required
def shift_dashboard_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_shift_access(request.user)

    stores = Store.objects.filter(
        is_active=True,
    ).order_by("name")

    current_shift = get_open_shift(
        cashier=request.user,
    )

    cash_sales = 0

    if current_shift is not None:
        cash_sales = calculate_shift_cash_sales(
            shift=current_shift,
        )

    recent_shifts = (
        WorkShift.objects
        .filter(cashier=request.user)
        .select_related("store")
        .order_by("-opened_at")[:20]
    )

    return render(
        request,
        "shifts/dashboard.html",
        {
            "stores": stores,
            "current_shift": current_shift,
            "cash_sales": cash_sales,
            "recent_shifts": recent_shifts,
            "open_form": OpenShiftForm(),
            "close_form": CloseShiftForm(),
        },
    )


@login_required
def manager_shift_list_view(
    request: HttpRequest,
) -> HttpResponse:
    if not request.user.is_superuser:
        if request.user.role not in {
            UserRole.MANAGER,
            UserRole.ADMIN,
        }:
            raise PermissionDenied(
                "Bạn không có quyền xem tất cả ca làm việc."
            )

    selected_status = request.GET.get(
        "status",
        "",
    )

    selected_store = request.GET.get(
        "store",
        "",
    )

    shifts = (
        WorkShift.objects
        .select_related(
            "store",
            "cashier",
        )
        .annotate(
            order_count=Count("orders"),
            order_revenue=Sum("orders__total"),
        )
        .order_by("-opened_at")
    )

    if selected_status:
        shifts = shifts.filter(
            status=selected_status,
        )

    if selected_store:
        shifts = shifts.filter(
            store_id=selected_store,
        )

    summary = shifts.aggregate(
        total_opening_cash=Sum("opening_cash"),
        total_expected_cash=Sum("expected_cash"),
        total_actual_cash=Sum("actual_cash"),
        total_difference=Sum("cash_difference"),
    )

    stores = Store.objects.filter(
        is_active=True,
    ).order_by("name")

    return render(
        request,
        "shifts/manager_list.html",
        {
            "shifts": shifts[:100],
            "stores": stores,
            "status_choices": ShiftStatus.choices,
            "selected_status": selected_status,
            "selected_store": selected_store,
            "summary": summary,
        },
    )


@login_required
@require_POST
def open_shift_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_shift_access(request.user)

    form = OpenShiftForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Thông tin mở ca không hợp lệ.",
        )
        return redirect("shifts:dashboard")

    try:
        shift = open_shift(
            cashier=request.user,
            store_id=form.cleaned_data["store_id"],
            opening_cash=form.cleaned_data[
                "opening_cash"
            ],
            note=form.cleaned_data[
                "opening_note"
            ],
        )
    except ShiftError as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        messages.success(
            request,
            f"Đã mở ca tại {shift.store.name}.",
        )

    return redirect("shifts:dashboard")


@login_required
@require_POST
def close_shift_view(
    request: HttpRequest,
    shift_id: int,
) -> HttpResponse:
    ensure_shift_access(request.user)

    pos_cart = PosCart(request)

    if len(pos_cart) > 0:
        messages.error(
            request,
            (
                "Không thể đóng ca vì đơn POS hiện tại "
                "vẫn còn sản phẩm chưa thanh toán."
            ),
        )

        return redirect("shifts:dashboard")

    shift = get_object_or_404(
        WorkShift,
        pk=shift_id,
        status=ShiftStatus.OPEN,
    )

    form = CloseShiftForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Thông tin đóng ca không hợp lệ.",
        )
        return redirect("shifts:dashboard")

    try:
        closed_shift = close_shift(
            shift_id=shift.id,
            cashier=request.user,
            actual_cash=form.cleaned_data[
                "actual_cash"
            ],
            note=form.cleaned_data[
                "closing_note"
            ],
        )
    except ShiftError as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        PosCart(request).clear()

        messages.success(
            request,
            (
                f"Đã đóng ca. Chênh lệch: "
                f"{closed_shift.cash_difference}đ."
            ),
        )

    return redirect("shifts:dashboard")
