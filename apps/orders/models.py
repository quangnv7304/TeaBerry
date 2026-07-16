import secrets
import string
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalog.models import Product
from apps.stores.models import Store

from apps.catalog.models import Product, ProductVariant


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Chờ xác nhận"
    CONFIRMED = "CONFIRMED", "Đã xác nhận"
    PREPARING = "PREPARING", "Đang pha chế"
    READY = "READY", "Sẵn sàng giao"
    DELIVERING = "DELIVERING", "Đang giao"
    COMPLETED = "COMPLETED", "Hoàn thành"
    CANCELLED = "CANCELLED", "Đã hủy"


class PaymentMethod(models.TextChoices):
    COD = "COD", "Thanh toán khi nhận hàng"
    BANK_TRANSFER = "BANK_TRANSFER", "Chuyển khoản ngân hàng"
    CASH = "CASH", "Tiền mặt tại quầy"


class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID", "Chưa thanh toán"
    PENDING = "PENDING", "Chờ xác nhận"
    PAID = "PAID", "Đã thanh toán"
    FAILED = "FAILED", "Thanh toán thất bại"
    REFUNDED = "REFUNDED", "Đã hoàn tiền"


class OrderSource(models.TextChoices):
    ONLINE = "ONLINE", "Website"
    POS = "POS", "Bán tại quầy"


class FulfillmentType(models.TextChoices):
    DELIVERY = "DELIVERY", "Giao hàng"
    PICKUP = "PICKUP", "Khách tự đến lấy"
    DINE_IN = "DINE_IN", "Dùng tại quán"


def generate_order_code() -> str:
    date_part = timezone.localtime().strftime("%y%m%d")
    alphabet = string.ascii_uppercase + string.digits

    random_part = "".join(
        secrets.choice(alphabet)
        for _ in range(6)
    )

    return f"TB-{date_part}-{random_part}"


class Order(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order_code = models.CharField(
        max_length=30,
        unique=True,
        default=generate_order_code,
        editable=False,
        verbose_name="Mã đơn hàng",
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
        verbose_name="Khách hàng",
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Cửa hàng",
    )

    source = models.CharField(
        max_length=20,
        choices=OrderSource.choices,
        default=OrderSource.ONLINE,
        verbose_name="Nguồn đơn hàng",
    )

    fulfillment_type = models.CharField(
        max_length=20,
        choices=FulfillmentType.choices,
        default=FulfillmentType.DELIVERY,
        verbose_name="Hình thức nhận hàng",
    )

    table_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Số bàn",
    )

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pos_orders",
        null=True,
        blank=True,
        verbose_name="Thu ngân",
    )
    shift = models.ForeignKey(
    "shifts.WorkShift",
    on_delete=models.SET_NULL,
    related_name="orders",
    null=True,
    blank=True,
    verbose_name="Ca làm việc",
)

    customer_name = models.CharField(
        max_length=150,
        verbose_name="Tên người nhận",
    )

    customer_phone = models.CharField(
        max_length=20,
        verbose_name="Số điện thoại",
    )

    customer_email = models.EmailField(
        blank=True,
        verbose_name="Email",
    )

    shipping_address = models.TextField(
        verbose_name="Địa chỉ giao hàng",
    )

    delivery_note = models.TextField(
        blank=True,
        verbose_name="Ghi chú giao hàng",
    )

    subtotal = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tạm tính",
    )

    shipping_fee = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Phí giao hàng",
    )

    discount = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Giảm giá",
    )

    voucher_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mã giảm giá",
    )

    loyalty_points_used = models.PositiveIntegerField(
        default=0,
        verbose_name="Điểm thưởng đã dùng",
    )

    loyalty_discount = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Giảm giá từ điểm thưởng",
    )

    @property
    def voucher_discount(self) -> int:
        return max(0, self.discount - self.loyalty_discount)

    total = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tổng thanh toán",
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
        verbose_name="Phương thức thanh toán",
    )

    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name="Trạng thái thanh toán",
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        verbose_name="Trạng thái đơn hàng",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Đơn hàng"
        verbose_name_plural = "Đơn hàng"

        indexes = [
            models.Index(
                fields=("order_code",),
            ),
            models.Index(
                fields=("status", "created_at"),
            ),
            models.Index(
                fields=("customer_phone",),
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(total__gte=0),
                name="order_total_gte_0",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name="order_subtotal_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return self.order_code


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Đơn hàng",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        null=True,
        blank=True,
        verbose_name="Sản phẩm",
    )

    product_name = models.CharField(
        max_length=200,
        verbose_name="Tên sản phẩm",
    )

    product_slug = models.CharField(
        max_length=220,
        blank=True,
        verbose_name="Slug sản phẩm",
    )
    product_variant = models.ForeignKey(
    ProductVariant,
    on_delete=models.PROTECT,
    related_name="order_items",
    null=True,
    blank=True,
    verbose_name="Biến thể sản phẩm",
)

    variant_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Kích thước",
    )

    sugar_label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mức đường",
    )

    ice_label = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Mức đá",
    )

    toppings = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Topping",
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )

    unit_price = models.PositiveBigIntegerField(
        verbose_name="Đơn giá sản phẩm",
    )

    topping_total = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tổng topping mỗi sản phẩm",
    )

    quantity = models.PositiveIntegerField(
        verbose_name="Số lượng",
    )

    line_total = models.PositiveBigIntegerField(
        verbose_name="Thành tiền",
    )

    class Meta:
        ordering = ("id",)
        verbose_name = "Sản phẩm trong đơn"
        verbose_name_plural = "Sản phẩm trong đơn"

        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="order_item_quantity_gt_0",
            ),
            models.CheckConstraint(
                condition=models.Q(line_total__gte=0),
                name="order_item_line_total_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} x {self.quantity}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Đơn hàng",
    )

    old_status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        blank=True,
        verbose_name="Trạng thái cũ",
    )

    new_status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        verbose_name="Trạng thái mới",
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="order_status_changes",
        null=True,
        blank=True,
        verbose_name="Người thực hiện",
    )

    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời gian",
    )

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Lịch sử trạng thái đơn"
        verbose_name_plural = "Lịch sử trạng thái đơn"

        indexes = [
            models.Index(
                fields=("order", "created_at"),
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.order.order_code}: "
            f"{self.old_status} → {self.new_status}"
            f"{self.product_name} × {self.quantity}"
        )
