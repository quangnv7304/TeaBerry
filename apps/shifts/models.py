from django.conf import settings
from django.db import models

from apps.stores.models import Store


class ShiftStatus(models.TextChoices):
    OPEN = "OPEN", "Đang mở"
    CLOSED = "CLOSED", "Đã đóng"


class WorkShift(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="work_shifts",
        verbose_name="Cửa hàng",
    )

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="work_shifts",
        verbose_name="Nhân viên",
    )

    status = models.CharField(
        max_length=20,
        choices=ShiftStatus.choices,
        default=ShiftStatus.OPEN,
        verbose_name="Trạng thái",
    )

    opening_cash = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tiền mặt đầu ca",
    )

    expected_cash = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tiền mặt dự kiến",
    )

    actual_cash = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Tiền mặt thực tế",
    )

    cash_difference = models.BigIntegerField(
        default=0,
        verbose_name="Chênh lệch tiền mặt",
    )

    opened_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Mở ca lúc",
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Đóng ca lúc",
    )

    opening_note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú mở ca",
    )

    closing_note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú đóng ca",
    )

    class Meta:
        ordering = ("-opened_at",)
        verbose_name = "Ca làm việc"
        verbose_name_plural = "Ca làm việc"

        constraints = [
            models.UniqueConstraint(
                fields=("store", "cashier"),
                condition=models.Q(status=ShiftStatus.OPEN),
                name="unique_open_shift_per_store_cashier",
            ),
            models.CheckConstraint(
                condition=models.Q(opening_cash__gte=0),
                name="shift_opening_cash_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(expected_cash__gte=0),
                name="shift_expected_cash_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.cashier} - {self.store} - "
            f"{self.get_status_display()}"
        )