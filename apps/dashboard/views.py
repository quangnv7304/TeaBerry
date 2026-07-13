from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.models import UserRole
from apps.orders.models import Order, OrderStatus


STAFF_ROLES = {
    UserRole.STAFF,
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_dashboard_access(user) -> None:
    if user.is_superuser:
        return

    if user.role not in STAFF_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền truy cập Dashboard."
        )


@login_required
def dashboard_home(request):
    ensure_dashboard_access(request.user)

    today = timezone.localdate()

    orders = (
        Order.objects
        .select_related(
            "store",
            "customer",
        )
        .prefetch_related("items")
        .order_by("-created_at")
    )

    today_orders = orders.filter(
        created_at__date=today,
    )

    completed_revenue = (
        today_orders
        .filter(status=OrderStatus.COMPLETED)
        .aggregate(total=Sum("total"))["total"]
        or 0
    )

    status_counts = {
        item["status"]: item["total"]
        for item in (
            today_orders
            .values("status")
            .annotate(total=Count("id"))
        )
    }

    context = {
        "orders": orders[:30],
        "today_order_count": today_orders.count(),
        "pending_count": status_counts.get(
            OrderStatus.PENDING,
            0,
        ),
        "preparing_count": status_counts.get(
            OrderStatus.PREPARING,
            0,
        ),
        "delivering_count": status_counts.get(
            OrderStatus.DELIVERING,
            0,
        ),
        "completed_revenue": completed_revenue,
        "status_choices": OrderStatus.choices,
    }

    return render(
        request,
        "dashboard/home.html",
        context,
    )