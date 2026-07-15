from dataclasses import dataclass

from django.db import transaction

from apps.catalog.models import (
    OptionChoice,
    OptionType,
    Product,
    ProductStatus,
    ProductTopping,
    ProductVariant,
)
from apps.orders.models import (
    FulfillmentType,
    Order,
    OrderItem,
    OrderSource,
    OrderStatus,
    OrderStatusHistory,
    PaymentMethod,
    PaymentStatus,
)
from apps.stores.models import Store

from .cart import PosCart


class PosOrderError(Exception):
    """Lỗi nghiệp vụ khi tạo đơn POS."""


@dataclass(frozen=True)
class ValidatedPosItem:
    product: Product
    variant: ProductVariant | None
    sugar_choice: OptionChoice | None
    ice_choice: OptionChoice | None
    toppings: list[ProductTopping]
    note: str
    unit_price: int
    topping_total: int
    quantity: int
    line_total: int


def validate_pos_cart_item(raw_item: dict) -> ValidatedPosItem:
    try:
        product_id = int(raw_item["product_id"])
        quantity = int(raw_item["quantity"])
    except (KeyError, TypeError, ValueError) as exc:
        raise PosOrderError("Dữ liệu món trong POS không hợp lệ.") from exc

    if quantity < 1 or quantity > 50:
        raise PosOrderError("Số lượng món không hợp lệ.")

    try:
        product = (
            Product.objects.select_related("store", "category").get(
                pk=product_id,
                is_active=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            )
        )
    except Product.DoesNotExist as exc:
        raise PosOrderError("Có sản phẩm không còn được bán.") from exc

    variant = None
    variant_id = raw_item.get("variant_id")
    if product.has_variants:
        if not variant_id:
            raise PosOrderError(f"{product.name} chưa có kích thước.")
        try:
            variant = ProductVariant.objects.get(
                pk=variant_id,
                product=product,
                is_available=True,
            )
        except ProductVariant.DoesNotExist as exc:
            raise PosOrderError(
                f"Kích thước của {product.name} không hợp lệ."
            ) from exc

    unit_price = int(variant.price if variant else product.base_price)

    sugar_choice = None
    if product.supports_sugar:
        try:
            sugar_choice = OptionChoice.objects.get(
                pk=raw_item.get("sugar_choice_id"),
                option_type=OptionType.SUGAR,
                is_active=True,
                product_options__product=product,
            )
        except OptionChoice.DoesNotExist as exc:
            raise PosOrderError(
                f"Mức đường của {product.name} không hợp lệ."
            ) from exc

    ice_choice = None
    if product.supports_ice:
        try:
            ice_choice = OptionChoice.objects.get(
                pk=raw_item.get("ice_choice_id"),
                option_type=OptionType.ICE,
                is_active=True,
                product_options__product=product,
            )
        except OptionChoice.DoesNotExist as exc:
            raise PosOrderError(
                f"Mức đá của {product.name} không hợp lệ."
            ) from exc

    try:
        requested_topping_ids = {
            int(topping["id"])
            for topping in raw_item.get("toppings", [])
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PosOrderError(
            f"Topping của {product.name} không hợp lệ."
        ) from exc

    toppings = list(
        ProductTopping.objects.filter(
            product=product,
            topping_id__in=requested_topping_ids,
            topping__is_available=True,
        ).select_related("topping")
    )
    actual_topping_ids = {
        relation.topping_id for relation in toppings
    }
    if requested_topping_ids != actual_topping_ids:
        raise PosOrderError(f"Topping của {product.name} không hợp lệ.")

    topping_total = sum(
        int(relation.topping.price) for relation in toppings
    )

    return ValidatedPosItem(
        product=product,
        variant=variant,
        sugar_choice=sugar_choice,
        ice_choice=ice_choice,
        toppings=toppings,
        note=str(raw_item.get("note", "")).strip(),
        unit_price=unit_price,
        topping_total=topping_total,
        quantity=quantity,
        line_total=(unit_price + topping_total) * quantity,
    )


@transaction.atomic
def create_pos_order(*, request, cleaned_data: dict) -> Order:
    cart = PosCart(request)
    raw_items = list(cart)
    if not raw_items:
        raise PosOrderError("Đơn tại quầy đang trống.")

    validated_items = [validate_pos_cart_item(item) for item in raw_items]
    store_ids = {item.product.store_id for item in validated_items}
    if len(store_ids) != 1:
        raise PosOrderError(
            "Một đơn POS chỉ được chứa món của một cửa hàng."
        )

    store = Store.objects.get(pk=next(iter(store_ids)), is_active=True)
    subtotal = sum(item.line_total for item in validated_items)
    customer_name = cleaned_data.get("customer_name", "").strip() or "Khách lẻ"
    fulfillment_type = cleaned_data["fulfillment_type"]
    table_number = cleaned_data.get("table_number", "").strip()
    shipping_address = (
        f"Dùng tại quán - Bàn {table_number}"
        if fulfillment_type == FulfillmentType.DINE_IN
        else "Khách nhận món tại quầy"
    )

    order = Order.objects.create(
        customer=None,
        store=store,
        source=OrderSource.POS,
        fulfillment_type=fulfillment_type,
        table_number=table_number,
        cashier=request.user,
        customer_name=customer_name,
        customer_phone=cleaned_data.get("customer_phone", ""),
        customer_email="",
        shipping_address=shipping_address,
        delivery_note=cleaned_data.get("note", "").strip(),
        subtotal=subtotal,
        shipping_fee=0,
        discount=0,
        total=subtotal,
        payment_method=PaymentMethod.CASH,
        payment_status=PaymentStatus.PAID,
        status=OrderStatus.CONFIRMED,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_slug=item.product.slug,
                product_variant=item.variant,
                variant_name=item.variant.name if item.variant else "",
                sugar_label=item.sugar_choice.label if item.sugar_choice else "",
                ice_label=item.ice_choice.label if item.ice_choice else "",
                toppings=[
                    {
                        "id": relation.topping.id,
                        "name": relation.topping.name,
                        "price": int(relation.topping.price),
                    }
                    for relation in item.toppings
                ],
                note=item.note,
                unit_price=item.unit_price,
                topping_total=item.topping_total,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in validated_items
        ]
    )
    OrderStatusHistory.objects.create(
        order=order,
        old_status="",
        new_status=OrderStatus.CONFIRMED,
        changed_by=request.user,
        note="Đơn được tạo và thanh toán tiền mặt tại POS.",
    )

    cart.clear()
    return order
