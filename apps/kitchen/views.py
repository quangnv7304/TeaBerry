from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.orders.models import OrderStatus
from apps.orders.services import (
    InvalidOrderStatusTransition,
    change_order_status,
)

from .permissions import ensure_kitchen_access
from .services import (
    get_kitchen_orders,
    serialize_kitchen_order,
)


@login_required
def kitchen_board_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_kitchen_access(request.user)

    orders = get_kitchen_orders()

    return render(
        request,
        "kitchen/board.html",
        {
            "orders": orders,
        },
    )


@login_required
@require_GET
def kitchen_orders_api_view(
    request: HttpRequest,
) -> JsonResponse:
    ensure_kitchen_access(request.user)

    orders = get_kitchen_orders()

    return JsonResponse(
        {
            "orders": [
                serialize_kitchen_order(order)
                for order in orders
            ],
        }
    )


@login_required
@require_POST
def kitchen_change_status_view(
    request: HttpRequest,
    order_id,
    new_status: str,
) -> HttpResponse:
    ensure_kitchen_access(request.user)

    allowed_kitchen_statuses = {
        OrderStatus.PREPARING,
        OrderStatus.READY,
        OrderStatus.COMPLETED,
    }

    if new_status not in allowed_kitchen_statuses:
        messages.error(
            request,
            "Trạng thái pha chế không hợp lệ.",
        )
        return redirect("kitchen:board")

    try:
        order = change_order_status(
            order_id=order_id,
            new_status=new_status,
            actor=request.user,
            note=request.POST.get("note", ""),
        )
    except InvalidOrderStatusTransition as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        messages.success(
            request,
            (
                f"Đơn {order.order_code} đã chuyển sang "
                f"{order.get_status_display()}."
            ),
        )

    return redirect("kitchen:board")