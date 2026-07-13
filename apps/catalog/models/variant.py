from django.db import models

from .product import Product


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Sản phẩm",
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Tên biến thể",
    )

    price = models.PositiveBigIntegerField(
        verbose_name="Giá bán",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name="Biến thể mặc định",
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Đang bán",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "price")
        verbose_name = "Biến thể sản phẩm"
        verbose_name_plural = "Biến thể sản phẩm"

        constraints = [
            models.UniqueConstraint(
                fields=("product", "name"),
                name="unique_variant_name_per_product",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.name}"