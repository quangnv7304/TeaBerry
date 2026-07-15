from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.inventory.models import (
    Ingredient,
    InventoryTransaction,
    InventoryTransactionType,
    Unit,
)
from apps.inventory.services import (
    InventoryError,
    import_stock,
)


@pytest.mark.django_db
def test_inventory_dashboard_requires_login(client):
    response = client.get(
        reverse("inventory:dashboard")
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_manager_can_view_inventory_dashboard(client):
    manager = User.objects.create_user(
        email="manager-inventory@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.MANAGER,
        is_staff=True,
    )

    client.force_login(manager)

    response = client.get(
        reverse("inventory:dashboard")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_import_stock_increases_balance():
    ingredient = Ingredient.objects.create(
        name="Sữa tươi",
        code="MILK-TEST",
        unit=Unit.MILLILITER,
        current_stock=Decimal("1000"),
        minimum_stock=Decimal("100"),
    )

    import_stock(
        ingredient_id=ingredient.id,
        quantity=Decimal("500"),
        note="Nhập thử",
    )

    ingredient.refresh_from_db()

    assert ingredient.current_stock == Decimal("1500")

    transaction = InventoryTransaction.objects.get(
        ingredient=ingredient,
        transaction_type=InventoryTransactionType.IMPORT,
    )

    assert transaction.quantity == Decimal("500")
    assert transaction.balance_after == Decimal("1500")


@pytest.mark.django_db
def test_import_stock_rejects_zero_quantity():
    ingredient = Ingredient.objects.create(
        name="Matcha test",
        code="MATCHA-TEST",
        unit=Unit.GRAM,
        current_stock=Decimal("100"),
        minimum_stock=Decimal("10"),
    )

    with pytest.raises(InventoryError):
        import_stock(
            ingredient_id=ingredient.id,
            quantity=0,
        )