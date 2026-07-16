from django.conf import settings
from django.db import models


class LoyaltyTier(models.TextChoices):
    MEMBER = "MEMBER", "Thành viên"
    SILVER = "SILVER", "Bạc"
    GOLD = "GOLD", "Vàng"
    PLATINUM = "PLATINUM", "Bạch kim"


class LoyaltyTransactionType(models.TextChoices):
    EARN = "EARN", "Tích điểm"
    REDEEM = "REDEEM", "Đổi điểm"
    ADJUST = "ADJUST", "Điều chỉnh"
    EXPIRE = "EXPIRE", "Điểm hết hạn"


class LoyaltyAccount(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loyalty_account",
        verbose_name="Khách hàng",
    )
    available_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Điểm khả dụng",
    )
    lifetime_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Tổng điểm tích lũy",
    )
    tier = models.CharField(
        max_length=20,
        choices=LoyaltyTier.choices,
        default=LoyaltyTier.MEMBER,
        verbose_name="Hạng thành viên",
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
        verbose_name = "Tài khoản điểm thưởng"
        verbose_name_plural = "Tài khoản điểm thưởng"

    def __str__(self) -> str:
        return f"{self.customer.email} - {self.available_points} điểm"


class LoyaltyTransaction(models.Model):
    account = models.ForeignKey(
        LoyaltyAccount,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Tài khoản điểm",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        related_name="loyalty_transactions",
        null=True,
        blank=True,
        verbose_name="Đơn hàng",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=LoyaltyTransactionType.choices,
        verbose_name="Loại giao dịch",
    )
    points = models.IntegerField(
        verbose_name="Số điểm thay đổi",
        help_text="Số dương khi cộng điểm, số âm khi trừ điểm.",
    )
    balance_after = models.PositiveIntegerField(
        verbose_name="Số dư sau giao dịch",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_loyalty_transactions",
        null=True,
        blank=True,
        verbose_name="Người thực hiện",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Giao dịch điểm thưởng"
        verbose_name_plural = "Giao dịch điểm thưởng"
        constraints = [
            models.UniqueConstraint(
                fields=("account", "order", "transaction_type"),
                condition=models.Q(
                    order__isnull=False,
                    transaction_type=LoyaltyTransactionType.EARN,
                ),
                name="unique_loyalty_earn_per_order",
            ),
            models.UniqueConstraint(
                fields=("account", "order", "transaction_type"),
                condition=models.Q(
                    order__isnull=False,
                    transaction_type=LoyaltyTransactionType.REDEEM,
                ),
                name="unique_loyalty_redeem_per_order",
            ),
            models.CheckConstraint(
                condition=~models.Q(points=0),
                name="loyalty_transaction_points_not_zero",
            ),
        ]

    def __str__(self) -> str:
        prefix = "+" if self.points > 0 else ""
        return f"{self.account.customer.email}: {prefix}{self.points} điểm"
