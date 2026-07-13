import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_product_list_page_loads(client):
    response = client.get(
        reverse("catalog:product-list")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_cart_page_loads(client):
    response = client.get(
        reverse("cart:detail")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_track_order_page_loads(client):
    response = client.get(
        reverse("orders:track")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_login_page_loads(client):
    response = client.get(
        reverse("accounts:login")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_register_page_loads(client):
    response = client.get(
        reverse("accounts:register")
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(
        reverse("dashboard:home")
    )

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url