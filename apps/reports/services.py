from datetime import timedelta

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.orders.models import (
    Order,
    OrderItem,
    OrderSource,
    OrderStatus,
)


REVENUE_STATUSES = (
    OrderStatus.COMPLETED,
)


def get_report_date_range(
    *,
    days: int = 7,
):
    end_date = timezone.localdate()
    start_date = end_date - timedelta(
        days=max(days - 1, 0)
    )

    return start_date, end_date


def get_completed_orders(
    *,
    start_date,
    end_date,
):
    return Order.objects.filter(
        status__in=REVENUE_STATUSES,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )


def get_report_summary(
    *,
    start_date,
    end_date,
) -> dict:
    orders = get_completed_orders(
        start_date=start_date,
        end_date=end_date,
    )

    aggregation = orders.aggregate(
        revenue=Sum("total"),
        order_count=Count("id"),
    )

    revenue = int(
        aggregation["revenue"] or 0
    )

    order_count = int(
        aggregation["order_count"] or 0
    )

    average_order_value = (
        revenue // order_count
        if order_count
        else 0
    )

    online_revenue = (
        orders.filter(
            source=OrderSource.ONLINE,
        ).aggregate(total=Sum("total"))["total"]
        or 0
    )

    pos_revenue = (
        orders.filter(
            source=OrderSource.POS,
        ).aggregate(total=Sum("total"))["total"]
        or 0
    )

    return {
        "revenue": int(revenue),
        "order_count": order_count,
        "average_order_value": int(
            average_order_value
        ),
        "online_revenue": int(
            online_revenue
        ),
        "pos_revenue": int(
            pos_revenue
        ),
    }


def get_daily_revenue(
    *,
    start_date,
    end_date,
) -> list[dict]:
    rows = (
        get_completed_orders(
            start_date=start_date,
            end_date=end_date,
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            revenue=Sum("total"),
            order_count=Count("id"),
        )
        .order_by("day")
    )

    row_map = {
        row["day"]: row
        for row in rows
    }

    data = []
    current_date = start_date

    while current_date <= end_date:
        row = row_map.get(current_date)

        data.append(
            {
                "date": current_date,
                "date_label": current_date.strftime(
                    "%d/%m"
                ),
                "revenue": int(
                    row["revenue"]
                    if row
                    else 0
                ),
                "order_count": int(
                    row["order_count"]
                    if row
                    else 0
                ),
            }
        )

        current_date += timedelta(days=1)

    return data


def get_top_products(
    *,
    start_date,
    end_date,
    limit: int = 10,
):
    item_revenue_expression = ExpressionWrapper(
        F("line_total"),
        output_field=DecimalField(
            max_digits=16,
            decimal_places=2,
        ),
    )

    return list(
        OrderItem.objects
        .filter(
            order__status__in=REVENUE_STATUSES,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date,
        )
        .values(
            "product_name",
            "variant_name",
        )
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum(
                item_revenue_expression
            ),
        )
        .order_by(
            "-quantity_sold",
            "-revenue",
        )[:limit]
    )