from django.contrib import admin

from .models import (
    Order,
    OrderItem,
    OrderStatusHistory,
)


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    can_delete = False

    readonly_fields = (
        "old_status",
        "new_status",
        "changed_by",
        "note",
        "created_at",
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False

    readonly_fields = (
        "product",
        "product_name",
        "variant_name",
        "sugar_label",
        "ice_label",
        "toppings",
        "note",
        "unit_price",
        "topping_total",
        "quantity",
        "line_total",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_code",
        "customer_name",
        "customer_phone",
        "voucher_code",
        "discount",
        "total",
        "payment_method",
        "payment_status",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "store",
        "created_at",
    )

    search_fields = (
        "order_code",
        "customer_name",
        "customer_phone",
        "customer_email",
        "voucher_code",
    )

    readonly_fields = (
        "id",
        "order_code",
        "subtotal",
        "shipping_fee",
        "discount",
        "loyalty_points_used",
        "loyalty_discount",
        "total",
        "created_at",
        "updated_at",
    )

    inlines = (
        OrderItemInline,
        OrderStatusHistoryInline,
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "order",
        "variant_name",
        "quantity",
        "line_total",
    )

    search_fields = (
        "product_name",
        "order__order_code",
    )

    list_select_related = (
        "order",
        "product",
    )
