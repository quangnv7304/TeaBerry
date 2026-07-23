from django.urls import path

from . import views
from .views import (
    TeaBerryLoginView,
    TeaBerryLogoutView,
    TeaBerryPasswordResetCompleteView,
    TeaBerryPasswordResetConfirmView,
    TeaBerryPasswordResetDoneView,
    TeaBerryPasswordResetView,
)

app_name = "accounts"

urlpatterns = [
    path(
        "loyalty/",
        views.loyalty_view,
        name="loyalty",
    ),
    path(
        "register/",
        views.register_view,
        name="register",
    ),
    path(
        "login/",
        TeaBerryLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        TeaBerryLogoutView.as_view(),
        name="logout",
    ),
    path(
        "password/change/",
        views.password_change_view,
        name="password-change",
    ),
    path(
        "password/reset/",
        TeaBerryPasswordResetView.as_view(),
        name="password-reset",
    ),
    path(
        "password/reset/done/",
        TeaBerryPasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        TeaBerryPasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path(
        "password/reset/complete/",
        TeaBerryPasswordResetCompleteView.as_view(),
        name="password-reset-complete",
    ),
    path(
    "addresses/",
    views.address_list_view,
    name="address-list",
),
path(
    "addresses/add/",
    views.address_create_view,
    name="address-create",
),
path(
    "addresses/<int:address_id>/edit/",
    views.address_update_view,
    name="address-update",
),
path(
    "addresses/<int:address_id>/default/",
    views.address_set_default_view,
    name="address-set-default",
),
path(
    "addresses/<int:address_id>/delete/",
    views.address_delete_view,
    name="address-delete",
),
]
