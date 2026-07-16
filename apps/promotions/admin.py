from django.contrib import admin

from .models import (
    Voucher,
    VoucherRedemption,
)


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "discount_type",
        "discount_value",
        "minimum_order_value",
        "used_count",
        "usage_limit",
        "starts_at",
        "ends_at",
        "is_active",
    )

    list_filter = (
        "discount_type",
        "is_active",
        "store",
        "starts_at",
        "ends_at",
    )

    search_fields = (
        "code",
        "name",
        "description",
    )

    readonly_fields = (
        "used_count",
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "store",
    )


@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = (
        "voucher",
        "order",
        "customer",
        "customer_phone",
        "discount_amount",
        "redeemed_at",
    )

    list_filter = (
        "voucher",
        "redeemed_at",
    )

    search_fields = (
        "voucher__code",
        "order__order_code",
        "customer__email",
        "customer_phone",
    )

    readonly_fields = (
        "voucher",
        "order",
        "customer",
        "customer_phone",
        "discount_amount",
        "redeemed_at",
    )

    list_select_related = (
        "voucher",
        "order",
        "customer",
    )