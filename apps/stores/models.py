from django.db import models


class Store(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Tên cửa hàng",
    )

    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Mã cửa hàng",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Số điện thoại",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Email",
    )

    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Địa chỉ",
    )

    is_accepting_orders = models.BooleanField(
        default=True,
        verbose_name="Đang nhận đơn",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Cửa hàng"
        verbose_name_plural = "Cửa hàng"

    def __str__(self) -> str:
        return self.name