from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import (
    OptionChoice,
    OptionType,
    Product,
    ProductOption,
    ProductStatus,
    ProductTopping,
    ProductVariant,
)

from .cart import SessionCart


@require_POST
def add_to_cart_view(
    request: HttpRequest,
) -> HttpResponse:
    product = get_object_or_404(
        Product.objects.select_related(
            "store",
            "category",
        ),
        pk=request.POST.get("product_id"),
        is_active=True,
        status=ProductStatus.ACTIVE,
        store__is_active=True,
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, min(quantity, 50))

    variant = None
    variant_id = request.POST.get("variant_id")

    if product.has_variants:
        variant = get_object_or_404(
            ProductVariant,
            pk=variant_id,
            product=product,
            is_available=True,
        )

    sugar_choice = None
    sugar_choice_id = request.POST.get(
        "sugar_choice_id"
    )

    if product.supports_sugar:
        sugar_choice = get_object_or_404(
            OptionChoice,
            pk=sugar_choice_id,
            option_type=OptionType.SUGAR,
            is_active=True,
            product_options__product=product,
        )

    ice_choice = None
    ice_choice_id = request.POST.get(
        "ice_choice_id"
    )

    if product.supports_ice:
        ice_choice = get_object_or_404(
            OptionChoice,
            pk=ice_choice_id,
            option_type=OptionType.ICE,
            is_active=True,
            product_options__product=product,
        )

    topping_ids = request.POST.getlist("toppings")

    product_toppings = list(
        ProductTopping.objects.filter(
            product=product,
            topping_id__in=topping_ids,
            topping__is_available=True,
        ).select_related("topping")
    )

    if len(product_toppings) != len(set(topping_ids)):
        messages.error(
            request,
            "Có topping không hợp lệ.",
        )
        return redirect(
            "catalog:product-detail",
            slug=product.slug,
        )

    cart = SessionCart(request)

    cart.add(
        product=product,
        variant=variant,
        sugar_choice=sugar_choice,
        ice_choice=ice_choice,
        toppings=product_toppings,
        quantity=quantity,
        note=request.POST.get("note", ""),
    )

    messages.success(
        request,
        f"Đã thêm {product.name} vào giỏ hàng.",
    )

    return redirect("cart:detail")


def cart_detail_view(
    request: HttpRequest,
) -> HttpResponse:
    cart = SessionCart(request)

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
        },
    )


@require_POST
def update_cart_item_view(
    request: HttpRequest,
    key: str,
) -> HttpResponse:
    cart = SessionCart(request)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(0, min(quantity, 50))

    cart.update_quantity(
        key=key,
        quantity=quantity,
    )

    messages.success(
        request,
        "Đã cập nhật giỏ hàng.",
    )

    return redirect("cart:detail")


@require_POST
def remove_cart_item_view(
    request: HttpRequest,
    key: str,
) -> HttpResponse:
    cart = SessionCart(request)
    cart.remove(key=key)

    messages.success(
        request,
        "Đã xóa sản phẩm khỏi giỏ hàng.",
    )

    if request.POST.get("buy_now"):
        return redirect("orders:checkout")
    return redirect("cart:detail")
