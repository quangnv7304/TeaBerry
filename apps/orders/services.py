from dataclasses import dataclass

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cart.cart import SessionCart
from apps.catalog.models import (
    OptionChoice,
    Product,
    ProductStatus,
    ProductTopping,
    ProductVariant,
)

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PaymentMethod,
    PaymentStatus,
)


class OrderCreationError(Exception):
    """Lỗi nghiệp vụ khi tạo đơn hàng."""


@dataclass(frozen=True)
class ValidatedCartItem:
    product: Product
    variant: ProductVariant | None
    sugar_choice: OptionChoice | None
    ice_choice: OptionChoice | None
    toppings: list[ProductTopping]
    quantity: int
    note: str
    unit_price: int
    topping_total: int
    line_total: int


def _validate_cart_item(item: dict) -> ValidatedCartItem:
    try:
        quantity = int(item["quantity"])
        product_id = int(item["product_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise OrderCreationError(
            "Dữ liệu giỏ hàng không hợp lệ."
        ) from exc

    if quantity <= 0 or quantity > 50:
        raise OrderCreationError(
            "Số lượng sản phẩm không hợp lệ."
        )

    try:
        product = Product.objects.select_related(
            "store",
            "category",
        ).get(
            pk=product_id,
            is_active=True,
            status=ProductStatus.ACTIVE,
            store__is_active=True,
            store__is_accepting_orders=True,
        )
    except Product.DoesNotExist as exc:
        raise OrderCreationError(
            "Có sản phẩm không còn được bán."
        ) from exc

    variant = None
    variant_id = item.get("variant_id")

    if product.has_variants:
        if not variant_id:
            raise OrderCreationError(
                f"Vui lòng chọn kích thước cho {product.name}."
            )

        try:
            variant = ProductVariant.objects.get(
                pk=variant_id,
                product=product,
                is_available=True,
            )
        except ProductVariant.DoesNotExist as exc:
            raise OrderCreationError(
                f"Kích thước của {product.name} không còn khả dụng."
            ) from exc

        unit_price = variant.price
    else:
        unit_price = product.base_price

    sugar_choice = None
    sugar_choice_id = item.get("sugar_choice_id")

    if product.supports_sugar:
        if not sugar_choice_id:
            raise OrderCreationError(
                f"Vui lòng chọn mức đường cho {product.name}."
            )

        try:
            sugar_choice = OptionChoice.objects.get(
                pk=sugar_choice_id,
                is_active=True,
                product_options__product=product,
                option_type="SUGAR",
            )
        except OptionChoice.DoesNotExist as exc:
            raise OrderCreationError(
                f"Mức đường của {product.name} không hợp lệ."
            ) from exc

    ice_choice = None
    ice_choice_id = item.get("ice_choice_id")

    if product.supports_ice:
        if not ice_choice_id:
            raise OrderCreationError(
                f"Vui lòng chọn mức đá cho {product.name}."
            )

        try:
            ice_choice = OptionChoice.objects.get(
                pk=ice_choice_id,
                is_active=True,
                product_options__product=product,
                option_type="ICE",
            )
        except OptionChoice.DoesNotExist as exc:
            raise OrderCreationError(
                f"Mức đá của {product.name} không hợp lệ."
            ) from exc

    requested_topping_ids = {
        int(topping["id"])
        for topping in item.get("toppings", [])
    }

    toppings = list(
        ProductTopping.objects.filter(
            product=product,
            topping_id__in=requested_topping_ids,
            topping__is_available=True,
        ).select_related("topping")
    )

    actual_topping_ids = {
        relation.topping_id
        for relation in toppings
    }

    if requested_topping_ids != actual_topping_ids:
        raise OrderCreationError(
            f"Có topping của {product.name} không còn hợp lệ."
        )

    topping_total = sum(
        relation.topping.price
        for relation in toppings
    )

    line_total = (
        unit_price + topping_total
    ) * quantity

    return ValidatedCartItem(
        product=product,
        variant=variant,
        sugar_choice=sugar_choice,
        ice_choice=ice_choice,
        toppings=toppings,
        quantity=quantity,
        note=str(item.get("note", "")).strip(),
        unit_price=unit_price,
        topping_total=topping_total,
        line_total=line_total,
    )


@transaction.atomic
def create_order_from_cart(
    *,
    request,
    cleaned_data: dict,
) -> Order:
    session_cart = SessionCart(request)
    raw_items = list(session_cart)

    if not raw_items:
        raise OrderCreationError(
            "Giỏ hàng đang trống."
        )

    validated_items = [
        _validate_cart_item(item)
        for item in raw_items
    ]

    store_ids = {
        item.product.store_id
        for item in validated_items
    }

    if len(store_ids) != 1:
        raise OrderCreationError(
            "Một đơn hàng chỉ được chứa sản phẩm của một cửa hàng."
        )

    store = validated_items[0].product.store

    if not store.is_active:
        raise OrderCreationError(
            "Cửa hàng hiện không hoạt động."
        )

    if not store.is_accepting_orders:
        raise OrderCreationError(
            "Cửa hàng đang tạm ngừng nhận đơn."
        )

    subtotal = sum(
        item.line_total
        for item in validated_items
    )

    shipping_fee = calculate_shipping_fee(
        subtotal=subtotal,
    )

    discount = 0

    total = max(
        0,
        subtotal + shipping_fee - discount,
    )

    payment_method = cleaned_data["payment_method"]

    if payment_method == PaymentMethod.BANK_TRANSFER:
        payment_status = PaymentStatus.PENDING
    else:
        payment_status = PaymentStatus.UNPAID

    customer = (
        request.user
        if request.user.is_authenticated
        else None
    )

    try:
        order = Order.objects.create(
            customer=customer,
            store=store,
            customer_name=cleaned_data["customer_name"],
            customer_phone=cleaned_data["customer_phone"],
            customer_email=cleaned_data.get(
                "customer_email",
                "",
            ),
            shipping_address=cleaned_data[
                "shipping_address"
            ],
            delivery_note=cleaned_data.get(
                "delivery_note",
                "",
            ),
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            discount=discount,
            total=total,
            payment_method=payment_method,
            payment_status=payment_status,
            
        )
    except IntegrityError as exc:
        raise OrderCreationError(
            "Không thể tạo mã đơn hàng. Vui lòng thử lại."
        ) from exc

    for item in validated_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            product_slug=item.product.slug,
            product_variant=item.variant,
            variant_name=(
                item.variant.name
                if item.variant
                else ""
            ),
            sugar_label=(
                item.sugar_choice.label
                if item.sugar_choice
                else ""
            ),
            ice_label=(
                item.ice_choice.label
                if item.ice_choice
                else ""
            ),
            toppings=[
                {
                    "id": relation.topping.id,
                    "name": relation.topping.name,
                    "price": relation.topping.price,
                }
                for relation in item.toppings
            ],
            note=item.note,
            unit_price=item.unit_price,
            topping_total=item.topping_total,
            quantity=item.quantity,
            line_total=item.line_total,
        )
        OrderStatusHistory.objects.create(
            order=order,
            old_status="",
            new_status=OrderStatus.PENDING,
            changed_by=customer,
            note="Đơn hàng được tạo.",
        )

    if order.payment_method == PaymentMethod.BANK_TRANSFER:
        from apps.payment.services import get_or_create_bank_transfer_payment

        get_or_create_bank_transfer_payment(order=order)

    session_cart.clear()

    recent_order_ids = request.session.get(
            "recent_order_ids",
            [],
        )

    recent_order_ids.append(
            str(order.id)
        )

    request.session["recent_order_ids"] = (
            recent_order_ids[-10:]
        )

    request.session.modified = True

    return order

ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.CONFIRMED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.CONFIRMED: {
        OrderStatus.PREPARING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PREPARING: {
        OrderStatus.READY,
    },
    OrderStatus.READY: {
        OrderStatus.DELIVERING,
        OrderStatus.COMPLETED,
    },
    OrderStatus.DELIVERING: {
        OrderStatus.COMPLETED,
    },
}


class InvalidOrderStatusTransition(Exception):
    """Không thể chuyển trạng thái đơn theo yêu cầu."""


@transaction.atomic
def change_order_status(
    *,
    order_id,
    new_status: str,
    actor,
    note: str = "",
) -> Order:
    try:
        order = (
            Order.objects
            .select_for_update()
            .get(pk=order_id)
        )
    except Order.DoesNotExist as exc:
        raise InvalidOrderStatusTransition(
            "Không tìm thấy đơn hàng."
        ) from exc

    old_status = order.status

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
        old_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise InvalidOrderStatusTransition(
            "Không thể chuyển đơn từ "
            f"{order.get_status_display()} "
            "sang trạng thái được yêu cầu."
        )

    order.status = new_status
    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status=new_status,
        changed_by=actor,
        note=note.strip(),
    )

    if new_status == OrderStatus.PREPARING:
        from apps.inventory.services import (
            InventoryError,
            consume_order_inventory,
        )

        try:
            consume_order_inventory(
                order_id=order.id,
                actor=actor,
            )
        except InventoryError as exc:
            raise InvalidOrderStatusTransition(
                str(exc)
            ) from exc

    if new_status == OrderStatus.CANCELLED:
        from apps.inventory.services import (
            restore_order_inventory,
        )

        restore_order_inventory(
            order_id=order.id,
            actor=actor,
            note=note,
        )

    return order

def ensure_order_staff(user) -> None:
    if not user.is_staff:
        raise PermissionDenied


@login_required
def staff_order_list_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_order_staff(request.user)

    selected_status = request.GET.get(
        "status",
        "",
    )

    orders = (
        Order.objects
        .select_related(
            "store",
            "customer",
        )
        .prefetch_related("items")
        .order_by("-created_at")
    )

    if selected_status:
        orders = orders.filter(
            status=selected_status,
        )

    return render(
        request,
        "orders/staff_order_list.html",
        {
            "orders": orders,
            "selected_status": selected_status,
            "status_choices": OrderStatus.choices,
        },
    )
@login_required
def staff_order_detail_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    ensure_order_staff(request.user)

    order = get_object_or_404(
        Order.objects
        .select_related(
            "store",
            "customer",
            "payment_transaction",
        )
        .prefetch_related(
            "items",
            "status_history__changed_by",
        ),
        pk=order_id,
    )

    payment = getattr(order, "payment_transaction", None)

    return render(
        request,
        "orders/staff_order_detail.html",
        {
            "order": order,
            "payment": payment,
        },
    )
@login_required
@require_POST
def staff_change_status_view(
    request: HttpRequest,
    order_id,
    new_status: str,
) -> HttpResponse:
    ensure_order_staff(request.user)

    valid_statuses = {
        choice[0]
        for choice in OrderStatus.choices
    }

    if new_status not in valid_statuses:
        raise PermissionDenied

    try:
        order = change_order_status(
            order_id=order_id,
            new_status=new_status,
            actor=request.user,
            note=request.POST.get("note", ""),
        )
    except InvalidOrderStatusTransition as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        messages.success(
            request,
            "Đã cập nhật trạng thái đơn thành "
            f"{order.get_status_display()}.",
        )

    return redirect(
        "orders:staff-detail",
        order_id=order_id,
    )

def calculate_shipping_fee(
    *,
    subtotal: int,
) -> int:
    free_shipping_threshold = 200_000
    default_shipping_fee = 20_000

    if subtotal >= free_shipping_threshold:
        return 0

    return default_shipping_fee
