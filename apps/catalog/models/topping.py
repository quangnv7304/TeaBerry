from django.db import models

from apps.stores.models import Store

from .product import Product


class Topping(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="toppings",
        verbose_name="Cửa hàng",
    )

    name = models.CharField(
        max_length=120,
        verbose_name="Tên topping",
    )

    price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Giá bán",
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Đang bán",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name = "Topping"
        verbose_name_plural = "Topping"

        constraints = [
            models.UniqueConstraint(
                fields=("store", "name"),
                name="unique_topping_name_per_store",
            )
        ]

    def __str__(self) -> str:
        return self.name


class ProductTopping(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_toppings",
        verbose_name="Sản phẩm",
    )

    topping = models.ForeignKey(
        Topping,
        on_delete=models.PROTECT,
        related_name="product_toppings",
        verbose_name="Topping",
    )

    max_quantity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Số lượng tối đa",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Topping của sản phẩm"
        verbose_name_plural = "Topping của sản phẩm"

        constraints = [
            models.UniqueConstraint(
                fields=("product", "topping"),
                name="unique_topping_per_product",
            ),
            models.CheckConstraint(
                condition=models.Q(max_quantity__gt=0),
                name="product_topping_max_quantity_gt_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.topping.name}"