from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.orders.models import (
    Order,
    OrderStatus,
    OrderStatusHistory,
    PaymentMethod,
    PaymentStatus,
)

from .models import PaymentTransaction, PaymentTransactionStatus


class PaymentError(Exception):
    """Payment business-rule error."""


def get_or_create_bank_transfer_payment(*, order: Order) -> PaymentTransaction:
    if order.payment_method != PaymentMethod.BANK_TRANSFER:
        raise PaymentError("Đơn hàng không sử dụng chuyển khoản.")

    bank_code = settings.TEABERRY_BANK_CODE.strip()
    bank_name = settings.TEABERRY_BANK_NAME.strip()
    bank_account = settings.TEABERRY_BANK_ACCOUNT.strip()
    bank_holder = settings.TEABERRY_BANK_HOLDER.strip()

    if not bank_code:
        raise PaymentError("Thiếu TEABERRY_BANK_CODE trong file .env.")
    if not bank_account:
        raise PaymentError("Thiếu TEABERRY_BANK_ACCOUNT trong file .env.")
    if not bank_holder:
        raise PaymentError("Thiếu TEABERRY_BANK_HOLDER trong file .env.")

    payment, created = PaymentTransaction.objects.get_or_create(
        order=order,
        defaults={
            "amount": order.total,
            "bank_code": bank_code,
            "bank_name": bank_name,
            "account_number": bank_account,
            "account_holder": bank_holder,
            "transfer_content": order.order_code,
        },
    )

    if not created and payment.amount != order.total:
        if payment.status == PaymentTransactionStatus.SUCCESS:
            raise PaymentError(
                "Giao dịch đã hoàn thành nên không thể đổi số tiền."
            )
        payment.amount = order.total
        payment.save(update_fields=["amount", "updated_at"])

    return payment


def build_vietqr_image_url(*, payment: PaymentTransaction) -> str:
    if not payment.bank_code:
        raise PaymentError("Chưa cấu hình mã ngân hàng.")
    if not payment.account_number:
        raise PaymentError("Chưa cấu hình số tài khoản.")
    if payment.amount <= 0:
        raise PaymentError("Số tiền thanh toán không hợp lệ.")
    if not payment.transfer_content.strip():
        raise PaymentError("Nội dung chuyển khoản đang để trống.")

    base_url = (
        "https://img.vietqr.io/image/"
        f"{payment.bank_code}-{payment.account_number}-compact2.png"
    )
    query = urlencode(
        {
            "amount": payment.amount,
            "addInfo": payment.transfer_content,
            "accountName": payment.account_holder,
        }
    )
    return f"{base_url}?{query}"


@transaction.atomic
def mark_customer_submitted(*, payment_id) -> PaymentTransaction:
    payment = (
        PaymentTransaction.objects.select_for_update()
        .select_related("order")
        .get(pk=payment_id)
    )
    if payment.status == PaymentTransactionStatus.SUCCESS:
        return payment

    payment.customer_submitted_at = timezone.now()
    payment.save(update_fields=["customer_submitted_at", "updated_at"])
    return payment


@transaction.atomic
def confirm_bank_transfer(
    *, payment_id, actor, provider_transaction_id: str
) -> PaymentTransaction:
    if not actor.is_authenticated:
        raise PaymentError("Bạn cần đăng nhập.")
    if not actor.is_staff and not actor.is_superuser:
        raise PaymentError("Bạn không có quyền xác nhận thanh toán.")

    payment = (
        PaymentTransaction.objects.select_for_update()
        .select_related("order")
        .get(pk=payment_id)
    )
    if payment.status == PaymentTransactionStatus.SUCCESS:
        raise PaymentError("Giao dịch đã được xác nhận trước đó.")

    transaction_code = provider_transaction_id.strip()
    if not transaction_code:
        raise PaymentError("Vui lòng nhập mã giao dịch ngân hàng.")

    duplicate_exists = (
        PaymentTransaction.objects.filter(
            provider_transaction_id=transaction_code,
            status=PaymentTransactionStatus.SUCCESS,
        )
        .exclude(pk=payment.pk)
        .exists()
    )
    if duplicate_exists:
        raise PaymentError("Mã giao dịch này đã được sử dụng.")

    order = Order.objects.select_for_update().get(pk=payment.order_id)
    if payment.amount != order.total:
        raise PaymentError("Số tiền giao dịch không khớp với đơn hàng.")

    now = timezone.now()
    payment.status = PaymentTransactionStatus.SUCCESS
    payment.provider_transaction_id = transaction_code
    payment.paid_at = now
    payment.confirmed_by = actor
    payment.save(
        update_fields=[
            "status",
            "provider_transaction_id",
            "paid_at",
            "confirmed_by",
            "updated_at",
        ]
    )

    old_order_status = order.status
    order.payment_status = PaymentStatus.PAID
    update_fields = ["payment_status", "updated_at"]
    if order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CONFIRMED
        update_fields.append("status")
    order.save(update_fields=update_fields)

    if old_order_status == OrderStatus.PENDING:
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_order_status,
            new_status=OrderStatus.CONFIRMED,
            changed_by=actor,
            note="Tự động xác nhận đơn sau khi nhận thanh toán.",
        )

    return payment
