from collections import defaultdict
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import F

from apps.orders.models import Order

from .models import (
    Ingredient,
    InventoryTransaction,
    InventoryTransactionType,
    Recipe,
)


class InventoryError(Exception):
    """Lỗi nghiệp vụ quản lý kho."""


def _build_order_requirements(
    *,
    order: Order,
) -> dict[int, Decimal]:
    requirements = defaultdict(Decimal)

    items = (
        order.items
        .select_related(
            "product",
            "product_variant",
        )
        .all()
    )

    for item in items:
        if item.product_variant_id is None:
            # Giai đoạn đầu chỉ trừ kho cho sản phẩm có biến thể.
            continue

        recipes = (
            Recipe.objects
            .filter(
                product_variant_id=item.product_variant_id,
            )
            .select_related("ingredient")
        )

        for recipe in recipes:
            requirements[recipe.ingredient_id] += (
                recipe.quantity
                * Decimal(item.quantity)
            )

    return dict(requirements)


@transaction.atomic
def import_stock(
    *,
    ingredient_id: int,
    quantity,
    actor=None,
    note: str = "",
) -> Ingredient:
    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise InventoryError(
            "Số lượng nhập kho phải lớn hơn 0."
        )

    ingredient = (
        Ingredient.objects
        .select_for_update()
        .get(
            pk=ingredient_id,
            is_active=True,
        )
    )

    ingredient.current_stock += quantity
    ingredient.save(
        update_fields=[
            "current_stock",
            "updated_at",
        ]
    )

    InventoryTransaction.objects.create(
        ingredient=ingredient,
        transaction_type=(
            InventoryTransactionType.IMPORT
        ),
        quantity=quantity,
        balance_after=ingredient.current_stock,
        created_by=actor,
        note=note.strip(),
    )

    return ingredient


@transaction.atomic
def consume_order_inventory(
    *,
    order_id,
    actor=None,
) -> None:
    order = (
        Order.objects
        .select_for_update()
        .prefetch_related("items")
        .get(pk=order_id)
    )

    requirements = _build_order_requirements(
        order=order,
    )

    if not requirements:
        return

    ingredients = {
        ingredient.id: ingredient
        for ingredient in (
            Ingredient.objects
            .select_for_update()
            .filter(
                id__in=requirements.keys(),
                is_active=True,
            )
        )
    }

    if len(ingredients) != len(requirements):
        raise InventoryError(
            "Có nguyên liệu trong công thức không còn hoạt động."
        )

    for ingredient_id, required_quantity in requirements.items():
        ingredient = ingredients[ingredient_id]

        already_consumed = (
            InventoryTransaction.objects
            .filter(
                order=order,
                ingredient=ingredient,
                transaction_type=(
                    InventoryTransactionType.CONSUME
                ),
            )
            .exists()
        )

        if already_consumed:
            continue

        if ingredient.current_stock < required_quantity:
            raise InventoryError(
                f"Không đủ {ingredient.name}. "
                f"Cần {required_quantity} {ingredient.unit}, "
                f"hiện còn {ingredient.current_stock} "
                f"{ingredient.unit}."
            )

    for ingredient_id, required_quantity in requirements.items():
        ingredient = ingredients[ingredient_id]

        already_consumed = (
            InventoryTransaction.objects
            .filter(
                order=order,
                ingredient=ingredient,
                transaction_type=(
                    InventoryTransactionType.CONSUME
                ),
            )
            .exists()
        )

        if already_consumed:
            continue

        ingredient.current_stock -= required_quantity
        ingredient.save(
            update_fields=[
                "current_stock",
                "updated_at",
            ]
        )

        try:
            InventoryTransaction.objects.create(
                ingredient=ingredient,
                order=order,
                transaction_type=(
                    InventoryTransactionType.CONSUME
                ),
                quantity=-required_quantity,
                balance_after=ingredient.current_stock,
                created_by=actor,
                note=(
                    f"Xuất nguyên liệu cho đơn "
                    f"{order.order_code}"
                ),
            )
        except IntegrityError:
            raise InventoryError(
                "Đơn hàng đã được trừ kho trước đó."
            )


@transaction.atomic
def restore_order_inventory(
    *,
    order_id,
    actor=None,
    note: str = "",
) -> None:
    order = (
        Order.objects
        .select_for_update()
        .get(pk=order_id)
    )

    consumed_transactions = list(
        InventoryTransaction.objects
        .select_related("ingredient")
        .filter(
            order=order,
            transaction_type=(
                InventoryTransactionType.CONSUME
            ),
        )
    )

    for consumed in consumed_transactions:
        already_restored = (
            InventoryTransaction.objects
            .filter(
                order=order,
                ingredient=consumed.ingredient,
                transaction_type=(
                    InventoryTransactionType.RESTORE
                ),
            )
            .exists()
        )

        if already_restored:
            continue

        ingredient = (
            Ingredient.objects
            .select_for_update()
            .get(pk=consumed.ingredient_id)
        )

        restored_quantity = abs(consumed.quantity)

        ingredient.current_stock += restored_quantity
        ingredient.save(
            update_fields=[
                "current_stock",
                "updated_at",
            ]
        )

        InventoryTransaction.objects.create(
            ingredient=ingredient,
            order=order,
            transaction_type=(
                InventoryTransactionType.RESTORE
            ),
            quantity=restored_quantity,
            balance_after=ingredient.current_stock,
            created_by=actor,
            note=(
                note.strip()
                or f"Hoàn nguyên liệu đơn {order.order_code}"
            ),
        )