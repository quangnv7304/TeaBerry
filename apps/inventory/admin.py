from django.contrib import admin

from .models import (
    Ingredient,
    Recipe,
    InventoryTransaction,
)


@admin.register(Ingredient)
class IngredientAdmin(
    admin.ModelAdmin,
):

    list_display = (
        "name",
        "current_stock",
        "minimum_stock",
        "unit",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )


@admin.register(Recipe)
class RecipeAdmin(
    admin.ModelAdmin,
):

    list_display = (
        "product_variant",
        "ingredient",
        "quantity",
    )


@admin.register(
    InventoryTransaction
)
class InventoryTransactionAdmin(
    admin.ModelAdmin,
):

    list_display = (
        "ingredient",
        "order",
        "transaction_type",
        "quantity",
        "balance_after",
        "created_by",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "ingredient",
        "created_at",
    )

    search_fields = (
        "ingredient__name",
        "ingredient__code",
        "order__order_code",
        "note",
    )

    readonly_fields = (
        "ingredient",
        "order",
        "transaction_type",
        "quantity",
        "balance_after",
        "created_by",
        "note",
        "created_at",
    )

    list_select_related = (
        "ingredient",
        "order",
        "created_by",
    )
