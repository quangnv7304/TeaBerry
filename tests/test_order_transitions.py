import pytest

from apps.orders.models import OrderStatus
from apps.orders.services import ALLOWED_STATUS_TRANSITIONS


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
        ),
        (
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
        ),
        (
            OrderStatus.PREPARING,
            OrderStatus.READY,
        ),
        (
            OrderStatus.READY,
            OrderStatus.COMPLETED,
        ),
    ],
)
def test_valid_order_status_transitions(
    current_status,
    new_status,
):
    assert (
        new_status
        in ALLOWED_STATUS_TRANSITIONS[
            current_status
        ]
    )


@pytest.mark.parametrize(
    ("current_status", "invalid_status"),
    [
        (
            OrderStatus.PENDING,
            OrderStatus.READY,
        ),
        (
            OrderStatus.CONFIRMED,
            OrderStatus.COMPLETED,
        ),
        (
            OrderStatus.COMPLETED,
            OrderStatus.PREPARING,
        ),
    ],
)
def test_invalid_order_status_transitions(
    current_status,
    invalid_status,
):
    allowed = ALLOWED_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    assert invalid_status not in allowed
