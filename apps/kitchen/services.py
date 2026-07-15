from django.db.models import Prefetch

from apps.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
)


KITCHEN_ACTIVE_STATUSES = (
    OrderStatus.CONFIRMED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
)


def get_kitchen_orders():
    items_queryset = OrderItem.objects.order_by("id")

    return (
        Order.objects
        .filter(status__in=KITCHEN_ACTIVE_STATUSES)
        .select_related(
            "store",
            "cashier",
        )
        .prefetch_related(
            Prefetch(
                "items",
                queryset=items_queryset,
            )
        )
        .order_by(
            "created_at",
        )
    )


def serialize_kitchen_order(order: Order) -> dict:
    return {
        "id": str(order.id),
        "order_code": order.order_code,
        "source": order.source,
        "source_label": order.get_source_display(),
        "fulfillment_type": order.fulfillment_type,
        "fulfillment_label": (
            order.get_fulfillment_type_display()
        ),
        "table_number": order.table_number,
        "customer_name": order.customer_name,
        "status": order.status,
        "status_label": order.get_status_display(),
        "created_at": order.created_at.isoformat(),
        "created_time": order.created_at.strftime(
            "%H:%M"
        ),
        "note": order.delivery_note,
        "items": [
            {
                "id": item.id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "variant_name": item.variant_name,
                "sugar_label": item.sugar_label,
                "ice_label": item.ice_label,
                "toppings": item.toppings,
                "note": item.note,
            }
            for item in order.items.all()
        ],
    }