from django.conf import settings
from django.db import models

from apps.catalog.models import ProductVariant
from apps.orders.models import Order


class Unit(models.TextChoices):
    GRAM = "g", "Gram"
    MILLILITER = "ml", "Milliliter"
    PIECE = "pcs", "Cái"


class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="recipes",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipes",
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("product_variant", "ingredient")

    def __str__(self):
        return f"{self.product_variant} - {self.ingredient}"


class InventoryTransactionType(models.TextChoices):
    IMPORT = "IMPORT", "Nhập kho"
    CONSUME = "CONSUME", "Xuất bán"
    RESTORE = "RESTORE", "Hoàn kho"
    ADJUST = "ADJUST", "Điều chỉnh"


class InventoryTransaction(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Nguyên liệu",
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
        null=True,
        blank=True,
        verbose_name="Đơn hàng",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=InventoryTransactionType.choices,
        verbose_name="Loại giao dịch",
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Số lượng thay đổi",
        help_text=(
            "Số dương khi nhập/hoàn kho, "
            "số âm khi xuất bán."
        ),
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Tồn kho sau giao dịch",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
        null=True,
        blank=True,
        verbose_name="Người thực hiện",
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Giao dịch kho"
        verbose_name_plural = "Giao dịch kho"

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "order",
                    "ingredient",
                    "transaction_type",
                ),
                condition=models.Q(
                    order__isnull=False,
                    transaction_type=(
                        InventoryTransactionType.CONSUME
                    ),
                ),
                name="unique_inventory_consume_per_order_ingredient",
            ),
            models.UniqueConstraint(
                fields=(
                    "order",
                    "ingredient",
                    "transaction_type",
                ),
                condition=models.Q(
                    order__isnull=False,
                    transaction_type=(
                        InventoryTransactionType.RESTORE
                    ),
                ),
                name="unique_inventory_restore_per_order_ingredient",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.ingredient.name}: "
            f"{self.quantity} {self.ingredient.unit}"
        )
