from django.contrib import admin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "amount",
        "bank_name",
        "status",
        "customer_submitted_at",
        "paid_at",
        "confirmed_by",
        "created_at",
    )

    list_filter = (
        "status",
        "bank_name",
        "created_at",
    )

    search_fields = (
        "order__order_code",
        "order__customer_name",
        "order__customer_phone",
        "provider_transaction_id",
    )

    readonly_fields = (
        "id",
        "order",
        "amount",
        "bank_code",
        "bank_name",
        "account_number",
        "account_holder",
        "transfer_content",
        "customer_submitted_at",
        "paid_at",
        "confirmed_by",
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "order",
        "confirmed_by",
    )