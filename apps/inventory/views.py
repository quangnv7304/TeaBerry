from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import UserRole

from .forms import ImportStockForm
from .models import Ingredient, InventoryTransaction
from .services import InventoryError, import_stock


INVENTORY_ROLES = {
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_inventory_access(user) -> None:
    if user.is_superuser:
        return

    if user.role not in INVENTORY_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền quản lý kho."
        )


@login_required
def inventory_dashboard_view(
    request: HttpRequest,
) -> HttpResponse:
    ensure_inventory_access(request.user)

    ingredients = (
        Ingredient.objects
        .filter(is_active=True)
        .order_by("name")
    )

    low_stock_ingredients = ingredients.filter(
        current_stock__lte=F("minimum_stock"),
    )

    recent_transactions = (
        InventoryTransaction.objects
        .select_related(
            "ingredient",
            "order",
            "created_by",
        )
        .order_by("-created_at")[:30]
    )

    return render(
        request,
        "inventory/dashboard.html",
        {
            "ingredients": ingredients,
            "low_stock_ingredients": low_stock_ingredients,
            "recent_transactions": recent_transactions,
        },
    )


@login_required
@require_POST
def import_stock_view(
    request: HttpRequest,
    ingredient_id: int,
) -> HttpResponse:
    ensure_inventory_access(request.user)

    ingredient = get_object_or_404(
        Ingredient,
        pk=ingredient_id,
        is_active=True,
    )

    form = ImportStockForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "Dữ liệu nhập kho không hợp lệ.",
        )
        return redirect("inventory:dashboard")

    try:
        import_stock(
            ingredient_id=ingredient.id,
            quantity=form.cleaned_data["quantity"],
            actor=request.user,
            note=form.cleaned_data["note"],
        )
    except InventoryError as exc:
        messages.error(
            request,
            str(exc),
        )
    else:
        messages.success(
            request,
            f"Đã nhập kho {ingredient.name}.",
        )

    return redirect("inventory:dashboard")