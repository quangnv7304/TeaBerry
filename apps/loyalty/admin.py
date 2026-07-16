from django.contrib import admin
from django.db import transaction

from .models import (
    LoyaltyAccount,
    LoyaltyTransaction,
    LoyaltyTransactionType,
)
from .services import update_tier


class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    can_delete = False
    readonly_fields = (
        "order",
        "transaction_type",
        "points",
        "balance_after",
        "note",
        "created_by",
        "created_at",
    )


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "available_points",
        "lifetime_points",
        "tier",
        "is_active",
        "updated_at",
    )
    list_filter = ("tier", "is_active")
    search_fields = ("customer__email", "customer__phone")
    readonly_fields = ("lifetime_points", "tier", "created_at", "updated_at")
    actions = ("add_100_points", "subtract_100_points", "lock", "unlock")
    inlines = (LoyaltyTransactionInline,)

    @admin.action(description="Cộng 100 điểm")
    def add_100_points(self, request, queryset):
        with transaction.atomic():
            for account in queryset.select_for_update():
                account.available_points += 100
                account.lifetime_points += 100
                account.save(update_fields=[
                    "available_points", "lifetime_points", "updated_at",
                ])
                update_tier(account)
                LoyaltyTransaction.objects.create(
                    account=account,
                    transaction_type=LoyaltyTransactionType.ADJUST,
                    points=100,
                    balance_after=account.available_points,
                    note=f"Quản trị viên {request.user} cộng điểm",
                    created_by=request.user,
                )

    @admin.action(description="Trừ 100 điểm")
    def subtract_100_points(self, request, queryset):
        with transaction.atomic():
            for account in queryset.select_for_update():
                deducted = min(100, account.available_points)
                if deducted == 0:
                    continue
                account.available_points -= deducted
                account.save(update_fields=["available_points", "updated_at"])
                LoyaltyTransaction.objects.create(
                    account=account,
                    transaction_type=LoyaltyTransactionType.ADJUST,
                    points=-deducted,
                    balance_after=account.available_points,
                    note=f"Quản trị viên {request.user} trừ điểm",
                    created_by=request.user,
                )

    @admin.action(description="Khóa tài khoản điểm")
    def lock(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Mở khóa tài khoản điểm")
    def unlock(self, request, queryset):
        queryset.update(is_active=True)


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "transaction_type",
        "points",
        "balance_after",
        "order",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = (
        "account__customer__email",
        "order__order_code",
        "note",
    )
    readonly_fields = (
        "account", "order", "transaction_type", "points", "balance_after",
        "note", "created_by", "created_at",
    )
