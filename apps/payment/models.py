import uuid

from django.db import models

from apps.orders.models import Order


class PaymentStatus(models.TextChoices):

    PENDING = "PENDING", "Đang chờ"

    SUCCESS = "SUCCESS", "Thành công"

    FAILED = "FAILED", "Thất bại"

    CANCELLED = "CANCELLED", "Đã hủy"


class Payment(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="payment",
    )

    amount = models.PositiveBigIntegerField()

    bank_name = models.CharField(
        max_length=100,
        blank=True,
    )

    account_number = models.CharField(
        max_length=50,
        blank=True,
    )

    account_holder = models.CharField(
        max_length=150,
        blank=True,
    )

    qr_content = models.CharField(
        max_length=255,
    )

    transaction_code = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return self.order.order_code