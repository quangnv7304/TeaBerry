from django.db import models

from .product import Product


class OptionType(models.TextChoices):
    SUGAR = "SUGAR", "Mức đường"
    ICE = "ICE", "Mức đá"


class OptionChoice(models.Model):
    option_type = models.CharField(
        max_length=20,
        choices=OptionType.choices,
        verbose_name="Loại tùy chọn",
    )

    code = models.CharField(
        max_length=30,
        verbose_name="Mã",
    )

    label = models.CharField(
        max_length=100,
        verbose_name="Tên hiển thị",
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
        ordering = (
            "option_type",
            "display_order",
            "label",
        )
        verbose_name = "Lựa chọn đường và đá"
        verbose_name_plural = "Lựa chọn đường và đá"

        constraints = [
            models.UniqueConstraint(
                fields=("option_type", "code"),
                name="unique_option_type_and_code",
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_option_type_display()} - {self.label}"


class ProductOption(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_options",
        verbose_name="Sản phẩm",
    )

    option_choice = models.ForeignKey(
        OptionChoice,
        on_delete=models.PROTECT,
        related_name="product_options",
        verbose_name="Lựa chọn",
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name="Lựa chọn mặc định",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (
            "option_choice__option_type",
            "option_choice__display_order",
        )
        verbose_name = "Tùy chọn của sản phẩm"
        verbose_name_plural = "Tùy chọn của sản phẩm"

        constraints = [
            models.UniqueConstraint(
                fields=("product", "option_choice"),
                name="unique_option_choice_per_product",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} - {self.option_choice.label}"
    