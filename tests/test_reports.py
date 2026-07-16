import pytest
from django.urls import reverse

from apps.accounts.models import User, UserRole


@pytest.mark.django_db
def test_reports_require_login(client):
    response = client.get(
        reverse(
            "reports:revenue-dashboard"
        )
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_manager_can_view_reports(client):
    manager = User.objects.create_user(
        email="reports-manager@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.MANAGER,
        is_staff=True,
    )

    client.force_login(manager)

    response = client.get(
        reverse(
            "reports:revenue-dashboard"
        )
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_cannot_view_reports(client):
    customer = User.objects.create_user(
        email="reports-customer@teaberry.local",
        password="StrongPassword123!",
        role=UserRole.CUSTOMER,
    )

    client.force_login(customer)

    response = client.get(
        reverse(
            "reports:revenue-dashboard"
        )
    )

    assert response.status_code == 403