from django.db import models

from apps.stores.models import Store

from .category import Category


class ProductStatus(models.TextChoices):
    DRAFT = "DRAFT", "Bản nháp"
    ACTIVE = "ACTIVE", "Đang bán"
    OUT_OF_STOCK = "OUT_OF_STOCK", "Hết hàng"
    INACTIVE = "INACTIVE", "Ngừng bán"


class Product(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Cửa hàng",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="Danh mục",
    )

    name = models.CharField(
        max_length=180,
        verbose_name="Tên sản phẩm",
    )

    slug = models.SlugField(
        max_length=200,
        verbose_name="Đường dẫn",
    )

    short_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Mô tả ngắn",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mô tả chi tiết",
    )

    base_price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Giá cơ bản",
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="Ảnh sản phẩm",
    )

    has_variants = models.BooleanField(
        default=False,
        verbose_name="Có biến thể",
    )

    supports_sugar = models.BooleanField(
        default=False,
        verbose_name="Cho chọn mức đường",
    )

    supports_ice = models.BooleanField(
        default=False,
        verbose_name="Cho chọn mức đá",
    )

    is_featured = models.BooleanField(
        default=False,
        verbose_name="Sản phẩm nổi bật",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
    )

    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        verbose_name="Trạng thái",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_featured", "name")
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"

        constraints = [
            models.UniqueConstraint(
                fields=("store", "slug"),
                name="unique_product_slug_per_store",
            )
        ]

    def __str__(self) -> str:
        return self.name