import uuid

from django.conf import settings
from django.db import models

from apps.orders.models import Order


class PaymentTransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Đang chờ"
    SUCCESS = "SUCCESS", "Thành công"
    FAILED = "FAILED", "Thất bại"
    CANCELLED = "CANCELLED", "Đã hủy"


class PaymentTransaction(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment_transaction",
        verbose_name="Đơn hàng",
    )

    amount = models.PositiveBigIntegerField(
        verbose_name="Số tiền",
    )

    bank_code = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Mã ngân hàng",
    )

    bank_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tên ngân hàng",
    )

    account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Số tài khoản",
    )

    account_holder = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Chủ tài khoản",
    )

    transfer_content = models.CharField(
        max_length=100,
        verbose_name="Nội dung chuyển khoản",
    )

    provider_transaction_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Mã giao dịch ngân hàng",
    )

    status = models.CharField(
        max_length=30,
        choices=PaymentTransactionStatus.choices,
        default=PaymentTransactionStatus.PENDING,
        verbose_name="Trạng thái",
    )

    customer_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Khách báo đã chuyển lúc",
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Thanh toán lúc",
    )

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="confirmed_payment_transactions",
        null=True,
        blank=True,
        verbose_name="Người xác nhận",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Giao dịch thanh toán"
        verbose_name_plural = "Giao dịch thanh toán"

        indexes = [
            models.Index(
                fields=("status", "created_at"),
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_transaction_amount_gt_0",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.order.order_code} - "
            f"{self.get_status_display()}"
        )