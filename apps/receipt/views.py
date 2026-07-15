from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.accounts.models import UserRole
from apps.orders.models import Order, OrderSource


RECEIPT_ROLES = {
    UserRole.STAFF,
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_receipt_access(user) -> None:
    if user.is_superuser:
        return

    if user.role not in RECEIPT_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền xem hóa đơn POS."
        )


@login_required
def receipt_detail_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    ensure_receipt_access(request.user)

    order = get_object_or_404(
        Order.objects
        .select_related(
            "store",
            "cashier",
        )
        .prefetch_related("items"),
        pk=order_id,
        source=OrderSource.POS,
    )

    return render(
        request,
        "receipt/detail.html",
        {
            "order": order,
        },
    )