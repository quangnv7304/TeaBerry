from django.db import models

from apps.stores.models import Store


class Category(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="categories",
        verbose_name="Cửa hàng",
    )

    name = models.CharField(
        max_length=120,
        verbose_name="Tên danh mục",
    )

    slug = models.SlugField(
        max_length=140,
        verbose_name="Đường dẫn",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mô tả",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Thứ tự hiển thị",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name")
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh mục"

        constraints = [
            models.UniqueConstraint(
                fields=("store", "slug"),
                name="unique_category_slug_per_store",
            )
        ]

    def __str__(self) -> str:
        return self.name