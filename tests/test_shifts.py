import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole
from apps.shifts.models import ShiftStatus, WorkShift
from apps.shifts.services import close_shift, open_shift
from apps.stores.models import Store


@pytest.fixture
def shift_store(db):
    return Store.objects.create(
        name="TeaBerry Shift",
        code="TB-SHIFT",
        is_active=True,
    )


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email="cashier-shift@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.STAFF,
        is_staff=True,
    )


@pytest.mark.django_db
def test_open_shift_creates_active_shift(
    cashier,
    shift_store,
):
    shift = open_shift(
        cashier=cashier,
        store_id=shift_store.id,
        opening_cash=500_000,
    )

    assert shift.status == ShiftStatus.OPEN
    assert shift.opening_cash == 500_000
    assert shift.expected_cash == 500_000


@pytest.mark.django_db
def test_close_shift_calculates_difference(
    cashier,
    shift_store,
):
    shift = open_shift(
        cashier=cashier,
        store_id=shift_store.id,
        opening_cash=500_000,
    )

    closed_shift = close_shift(
        shift_id=shift.id,
        cashier=cashier,
        actual_cash=490_000,
    )

    assert closed_shift.status == ShiftStatus.CLOSED
    assert closed_shift.expected_cash == 500_000
    assert closed_shift.cash_difference == -10_000


@pytest.mark.django_db
def test_pos_redirects_without_open_shift(
    client,
    cashier,
):
    client.force_login(cashier)

    response = client.get(
        reverse("pos:home")
    )

    assert response.status_code == 302
    assert response.url == reverse(
        "shifts:dashboard"
    )


@pytest.mark.django_db
def test_manager_can_view_all_shifts(
    client,
):
    manager = User.objects.create_user(
        email="shift-manager@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.MANAGER,
        is_staff=True,
    )

    client.force_login(manager)

    response = client.get(
        reverse("shifts:manager-list")
    )

    assert response.status_code == 200