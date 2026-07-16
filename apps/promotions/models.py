from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.orders.models import Order
from apps.stores.models import Store


class DiscountType(models.TextChoices):
    FIXED = "FIXED", "Giảm số tiền cố định"
    PERCENT = "PERCENT", "Giảm theo phần trăm"


class Voucher(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Mã giảm giá",
    )

    name = models.CharField(
        max_length=150,
        verbose_name="Tên chương trình",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Mô tả",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="vouchers",
        null=True,
        blank=True,
        verbose_name="Cửa hàng áp dụng",
        help_text=(
            "Để trống nếu mã áp dụng cho tất cả cửa hàng."
        ),
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        verbose_name="Loại giảm giá",
    )

    discount_value = models.PositiveBigIntegerField(
        verbose_name="Giá trị giảm",
        help_text=(
            "Nếu giảm phần trăm, nhập từ 1 đến 100."
        ),
    )

    maximum_discount = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Mức giảm tối đa",
        help_text=(
            "Chỉ áp dụng cho giảm theo phần trăm."
        ),
    )

    minimum_order_value = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Giá trị đơn tối thiểu",
    )

    usage_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Tổng lượt sử dụng tối đa",
        help_text="Để trống nếu không giới hạn.",
    )

    usage_limit_per_customer = models.PositiveIntegerField(
        default=1,
        verbose_name="Lượt dùng tối đa mỗi khách",
    )

    used_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        verbose_name="Số lượt đã sử dụng",
    )

    starts_at = models.DateTimeField(
        verbose_name="Bắt đầu lúc",
    )

    ends_at = models.DateTimeField(
        verbose_name="Kết thúc lúc",
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
        ordering = (
            "-created_at",
        )

        verbose_name = "Mã giảm giá"
        verbose_name_plural = "Mã giảm giá"

        indexes = [
            models.Index(
                fields=(
                    "code",
                    "is_active",
                ),
            ),
            models.Index(
                fields=(
                    "starts_at",
                    "ends_at",
                ),
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    discount_value__gt=0,
                ),
                name="voucher_discount_value_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    usage_limit_per_customer__gt=0,
                ),
                name="voucher_customer_limit_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    ends_at__gt=models.F("starts_at"),
                ),
                name="voucher_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    @property
    def is_available_now(self) -> bool:
        now = timezone.now()

        if not self.is_active:
            return False

        if now < self.starts_at or now > self.ends_at:
            return False

        if (
            self.usage_limit is not None
            and self.used_count >= self.usage_limit
        ):
            return False

        return True
class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.PROTECT,
        related_name="redemptions",
        verbose_name="Mã giảm giá",
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="voucher_redemption",
        verbose_name="Đơn hàng",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="voucher_redemptions",
        null=True,
        blank=True,
        verbose_name="Khách hàng",
    )

    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Số điện thoại khách",
    )

    discount_amount = models.PositiveBigIntegerField(
        verbose_name="Số tiền đã giảm",
    )

    redeemed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Sử dụng lúc",
    )

    class Meta:
        ordering = (
            "-redeemed_at",
        )

        verbose_name = "Lượt sử dụng mã"
        verbose_name_plural = "Lượt sử dụng mã"

        indexes = [
            models.Index(
                fields=(
                    "voucher",
                    "customer",
                ),
            ),
            models.Index(
                fields=(
                    "voucher",
                    "customer_phone",
                ),
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.voucher.code} - "
            f"{self.order.order_code}"
        )