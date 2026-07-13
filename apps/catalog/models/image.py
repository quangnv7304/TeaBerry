from django.db import models

from .product import Product


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Sản phẩm",
    )

    image = models.ImageField(
        upload_to="products/gallery/",
        verbose_name="Ảnh",
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Mô tả ảnh",
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name="Ảnh chính",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = (
            "-is_primary",
            "display_order",
            "id",
        )
        verbose_name = "Ảnh sản phẩm"
        verbose_name_plural = "Ảnh sản phẩm"

    def __str__(self) -> str:
        return f"Ảnh của {self.product.name}"
    