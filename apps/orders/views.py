from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.cart.cart import SessionCart

from .forms import CheckoutForm
from .models import Order
from .services import (
    OrderCreationError,
    calculate_shipping_fee,
    create_order_from_cart,
    staff_change_status_view,
    staff_order_detail_view,
    staff_order_list_view,
)
from apps.accounts.models import Address


@require_http_methods(["GET", "POST"])
def track_order_view(request: HttpRequest) -> HttpResponse:
    order = None
    error_message = ""

    if request.method == "POST":
        order_code = request.POST.get("order_code", "").strip().upper()
        customer_phone = request.POST.get("customer_phone", "").strip()
        order = (
            Order.objects.prefetch_related("items", "status_history")
            .filter(order_code=order_code, customer_phone=customer_phone)
            .first()
        )
        if order is None:
            error_message = "Không tìm thấy đơn hàng phù hợp."

    return render(
        request,
        "orders/track_order.html",
        {"order": order, "error_message": error_message},
    )


@require_http_methods(["GET", "POST"])
def checkout_view(
    request: HttpRequest,
) -> HttpResponse:
    cart = SessionCart(request)

    if len(cart) == 0:
        messages.warning(
            request,
            "Giỏ hàng đang trống.",
        )
        return redirect("cart:detail")

    initial_data = {}

    if request.user.is_authenticated:
        initial_data = {
            "customer_name": request.user.full_name,
            "customer_email": request.user.email,
            "customer_phone": request.user.phone or "",
        }

        default_address = Address.objects.filter(
            user=request.user,
            is_active=True,
            is_default=True,
        ).first()

        if default_address:
            initial_data.update({
                "customer_name": default_address.recipient_name,
                "customer_phone": default_address.recipient_phone,
                "shipping_address": default_address.full_address,
                "delivery_note": default_address.delivery_note,
            })

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                order = create_order_from_cart(
                    request=request,
                    cleaned_data=form.cleaned_data,
                )
            except OrderCreationError as exc:
                messages.error(
                    request,
                    str(exc),
                )
            else:
                messages.success(
                    request,
                    "Đặt hàng thành công.",
                )

                if order.payment_method == "BANK_TRANSFER":
                    return redirect(
                        "orders:bank-transfer",
                        order_id=order.id,
                    )

                return redirect(
                    "orders:success",
                    order_id=order.id,
                )
    else:
        form = CheckoutForm(
            initial=initial_data,
        )

    subtotal = cart.get_total_price()
    shipping_fee = calculate_shipping_fee(
        subtotal=subtotal,
    )

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "total": subtotal + shipping_fee,
        },
    )


def order_success_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    order = _get_accessible_order(
        request=request,
        order_id=order_id,
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
        },
    )


def bank_transfer_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    order = _get_accessible_order(
        request=request,
        order_id=order_id,
    )

    return render(
        request,
        "orders/bank_transfer.html",
        {
            "order": order,
        },
    )


def _get_accessible_order(
    *,
    request: HttpRequest,
    order_id,
) -> Order:
    queryset = (
        Order.objects
        .select_related("store", "customer")
        .prefetch_related("items")
    )

    if request.user.is_authenticated:
        if request.user.is_staff:
            return queryset.get(pk=order_id)

        return queryset.get(
            pk=order_id,
            customer=request.user,
        )

    recent_order_ids = request.session.get(
        "recent_order_ids",
        [],
    )

    if str(order_id) not in recent_order_ids:
        from django.http import Http404

        raise Http404

    return queryset.get(pk=order_id)

@login_required
def customer_order_list_view(
    request: HttpRequest,
) -> HttpResponse:
    orders = (
        Order.objects
        .filter(customer=request.user)
        .select_related("store")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/customer_order_list.html",
        {
            "orders": orders,
        },
    )

@login_required
def customer_order_detail_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    order = get_object_or_404(
        Order.objects
        .select_related("store")
        .prefetch_related(
            "items",
            "status_history",
        ),
        pk=order_id,
        customer=request.user,
    )

    return render(
        request,
        "orders/customer_order_detail.html",
        {
            "order": order,
        },
    )
