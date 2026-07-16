from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from apps.accounts.models import UserRole
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
    OrderSource,
)
from apps.shifts.services import get_open_shift

from .cart import PosCart
from .forms import PosCheckoutForm
from .services import PosOrderError, create_pos_order


POS_ROLES = {
    UserRole.STAFF,
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_pos_access(user) -> None:
    if not user.is_authenticated:
        raise PermissionDenied

    if user.is_superuser:
        return

    if user.role not in POS_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền sử dụng POS."
        )


def get_required_open_shift(
    *,
    request: HttpRequest,
):
    shift = get_open_shift(
        cashier=request.user,
    )

    if shift is None:
        messages.warning(
            request,
            "Bạn chưa mở ca bán hàng.",
        )

    return shift


@login_required
def pos_home_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_pos_access(request.user)

    products = (
        Product.objects
        .filter(
            is_active=True,
            status=ProductStatus.ACTIVE,
            store__is_active=True,
        )
        .select_related(
            "store",
            "category",
        )
        .prefetch_related(
            "variants",
            "product_options__option_choice",
            "product_toppings__topping",
        )
        .order_by(
            "category__display_order",
            "name",
        )
    )

    cart = PosCart(request)

    return render(
        request,
        "pos/home.html",
        {
            "products": products,
            "cart": cart,
        },
    )

@login_required
@require_POST
def pos_add_item_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_pos_access(request.user)

    if get_required_open_shift(
        request=request,
    ) is None:
        return redirect("shifts:dashboard")

    product = get_object_or_404(
        Product.objects.select_related("store"),
        pk=request.POST.get("product_id"),
        is_active=True,
        status=ProductStatus.ACTIVE,
        store__is_active=True,
    )

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

    toppings = list(
        ProductTopping.objects.filter(
            product=product,
            topping_id__in=topping_ids,
            topping__is_available=True,
        ).select_related("topping")
    )

    if len(toppings) != len(set(topping_ids)):
        messages.error(
            request,
            "Có topping không hợp lệ.",
        )
        return redirect("pos:home")

    try:
        quantity = int(
            request.POST.get("quantity", 1)
        )
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, min(quantity, 50))

    cart = PosCart(request)

    cart.add(
        product=product,
        variant=variant,
        sugar_choice=sugar_choice,
        ice_choice=ice_choice,
        toppings=toppings,
        quantity=quantity,
        note=request.POST.get("note", ""),
    )

    messages.success(
        request,
        f"Đã thêm {product.name} vào đơn.",
    )

    return redirect("pos:home")


@login_required
@require_POST
def pos_update_item_view(
    request: HttpRequest,
    item_key: str,
) -> HttpResponse:
    ensure_pos_access(request.user)

    if get_required_open_shift(
        request=request,
    ) is None:
        return redirect("shifts:dashboard")

    try:
        quantity = int(
            request.POST.get("quantity", 1)
        )
    except (TypeError, ValueError):
        quantity = 1

    cart = PosCart(request)
    cart.update_quantity(
        item_key=item_key,
        quantity=quantity,
    )

    return redirect("pos:home")


@login_required
@require_POST
def pos_remove_item_view(
    request: HttpRequest,
    item_key: str,
) -> HttpResponse:
    ensure_pos_access(request.user)

    if get_required_open_shift(
        request=request,
    ) is None:
        return redirect("shifts:dashboard")

    cart = PosCart(request)
    cart.remove(item_key=item_key)

    messages.success(
        request,
        "Đã xóa món khỏi đơn.",
    )

    return redirect("pos:home")


@login_required
@require_POST
def pos_clear_cart_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_pos_access(request.user)

    if get_required_open_shift(
        request=request,
    ) is None:
        return redirect("shifts:dashboard")

    cart = PosCart(request)
    cart.clear()

    messages.success(
        request,
        "Đã làm trống đơn tại quầy.",
    )

    return redirect("pos:home")

@login_required
def pos_checkout_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_pos_access(request.user)

    if get_required_open_shift(
        request=request,
    ) is None:
        return redirect("shifts:dashboard")

    cart = PosCart(request)

    if len(cart) == 0:
        messages.warning(
            request,
            "Đơn tại quầy đang trống.",
        )
        return redirect("pos:home")

    if request.method == "POST":
        form = PosCheckoutForm(
            request.POST
        )

        if form.is_valid():
            try:
                order = create_pos_order(
                    request=request,
                    cleaned_data=form.cleaned_data,
                )
            except PosOrderError as exc:
                messages.error(
                    request,
                    str(exc),
                )
            else:
                messages.success(
                    request,
                    (
                        f"Đã tạo đơn "
                        f"{order.order_code} thành công."
                    ),
                )

                return redirect(
                    "pos:success",
                    order_id=order.id,
                )
    else:
        form = PosCheckoutForm(
            initial={
                "fulfillment_type": (
                    FulfillmentType.PICKUP
                ),
                "customer_name": "Khách lẻ",
            }
        )

    return render(
        request,
        "pos/checkout.html",
        {
            "cart": cart,
            "form": form,
        },
    )


@login_required
def pos_order_success_view(
    request: HttpRequest,
    order_id,
) -> HttpResponse:
    ensure_pos_access(request.user)

    order = get_object_or_404(
        Order.objects
        .select_related(
            "store",
            "cashier",
        )
        .prefetch_related("items"),
        pk=order_id,
        source=OrderSource.POS,
    )

    return render(
        request,
        "pos/order_success.html",
        {
            "order": order,
        },
    )
