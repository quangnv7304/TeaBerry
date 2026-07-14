from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.orders.models import Order

from .models import PaymentTransaction
from .services import (
    PaymentError,
    build_vietqr_image_url,
    confirm_bank_transfer,
    get_or_create_bank_transfer_payment,
    mark_customer_submitted,
)


def get_accessible_order(
    *,
    request: HttpRequest,
    order_id,
) -> Order:
    queryset = Order.objects.select_related(
        "customer",
        "store",
    )

    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return get_object_or_404(
                queryset,
                pk=order_id,
            )

        return get_object_or_404(
            queryset,
            pk=order_id,
            customer=request.user,
        )

    recent_order_ids = request.session.get(
        "recent_order_ids",
        [],
    )

    if str(order_id) not in recent_order_ids:
        raise Http404(
            "Không tìm thấy đơn hàng."
        )

    return get_object_or_404(
        queryset,
        pk=order_id,
    )


def bank_transfer_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    order = get_accessible_order(
        request=request,
        order_id=order_id,
    )

    try:
        payment = get_or_create_bank_transfer_payment(
            order=order,
        )

        qr_url = build_vietqr_image_url(
            payment=payment,
        )
    except PaymentError as exc:
        messages.error(
            request,
            str(exc),
        )

        return redirect(
            "orders:success",
            order_id=order.id,
        )

    return render(
        request,
        "payment/bank_transfer.html",
        {
            "order": order,
            "payment": payment,
            "qr_image_url": qr_url,
        },
    )


@require_POST
def customer_submitted_view(
    request: HttpRequest,
    payment_id,
) -> HttpResponse:
    payment = get_object_or_404(
        PaymentTransaction.objects.select_related(
            "order",
        ),
        pk=payment_id,
    )

    get_accessible_order(
        request=request,
        order_id=payment.order_id,
    )

    mark_customer_submitted(
        payment_id=payment.id,
    )

    messages.success(
        request,
        (
            "TeaBerry đã nhận thông báo. "
            "Nhân viên sẽ kiểm tra giao dịch."
        ),
    )

    return redirect(
        "payment:bank-transfer",
        order_id=payment.order_id,
    )


@login_required
@require_POST
def staff_confirm_payment_view(
    request: HttpRequest,
    payment_id,
) -> HttpResponse:
    payment = get_object_or_404(
        PaymentTransaction.objects.select_related(
            "order",
        ),
        pk=payment_id,
    )

    try:
        confirm_bank_transfer(
            payment_id=payment.id,
            actor=request.user,
            provider_transaction_id=request.POST.get(
                "provider_transaction_id",
                "",
            ),
        )
    except PaymentError as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        messages.success(
            request,
            "Đã xác nhận thanh toán thành công.",
        )

    return redirect(
        "orders:staff-detail",
        order_id=payment.order_id,
    )
