from django.contrib import admin

from .models import WorkShift


@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = (
        "cashier",
        "store",
        "status",
        "opening_cash",
        "expected_cash",
        "actual_cash",
        "cash_difference",
        "opened_at",
        "closed_at",
    )

    list_filter = (
        "status",
        "store",
        "opened_at",
    )

    search_fields = (
        "cashier__email",
        "cashier__full_name",
        "store__name",
    )

    readonly_fields = (
        "expected_cash",
        "cash_difference",
        "opened_at",
        "closed_at",
    )

    list_select_related = (
        "cashier",
        "store",
    )