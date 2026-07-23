import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import User


@pytest.fixture(autouse=True)
def use_test_staticfiles_storage(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {
            "BACKEND": (
                "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    }


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="customer@example.com",
        password="CurrentPassword123!",
        full_name="Khách hàng",
    )


def test_password_change_requires_login(client):
    response = client.get(reverse("accounts:password-change"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_password_change_rejects_wrong_current_password(client, user):
    client.force_login(user)

    response = client.post(
        reverse("accounts:password-change"),
        {
            "old_password": "WrongPassword123!",
            "new_password1": "NewSecurePassword456!",
            "new_password2": "NewSecurePassword456!",
        },
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.check_password("CurrentPassword123!")
    assert "old_password" in response.context["form"].errors


def test_password_change_updates_password_and_keeps_session(client, user):
    client.force_login(user)

    response = client.post(
        reverse("accounts:password-change"),
        {
            "old_password": "CurrentPassword123!",
            "new_password1": "NewSecurePassword456!",
            "new_password2": "NewSecurePassword456!",
        },
        follow=True,
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.check_password("NewSecurePassword456!")
    assert response.context["user"].is_authenticated
    assert list(response.context["messages"])[0].message == (
        "Đổi mật khẩu thành công."
    )


def test_forgot_password_sends_link_and_resets_password(client, user):
    response = client.post(
        reverse("accounts:password-reset"),
        {"email": user.email},
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:password-reset-done")
    assert len(mail.outbox) == 1
    assert user.email in mail.outbox[0].to

    reset_url = next(
        line.strip()
        for line in mail.outbox[0].body.splitlines()
        if "/account/password/reset/" in line
    )
    reset_path = reset_url.split("testserver", 1)[1]

    response = client.get(reset_path)
    assert response.status_code == 302

    response = client.post(
        response.url,
        {
            "new_password1": "RecoveredPassword789!",
            "new_password2": "RecoveredPassword789!",
        },
    )

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == reverse("accounts:password-reset-complete")
    assert user.check_password("RecoveredPassword789!")


def test_forgot_password_does_not_reveal_unknown_email(client, db):
    response = client.post(
        reverse("accounts:password-reset"),
        {"email": "unknown@example.com"},
    )

    assert response.status_code == 302
    assert response.url == reverse("accounts:password-reset-done")
    assert mail.outbox == []
