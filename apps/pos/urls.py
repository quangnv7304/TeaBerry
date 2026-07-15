from django.urls import path

from . import views

app_name = "pos"

urlpatterns = [
    path(
        "",
        views.pos_home_view,
        name="home",
    ),
    path(
        "items/add/",
        views.pos_add_item_view,
        name="item-add",
    ),
    path(
        "items/<path:item_key>/update/",
        views.pos_update_item_view,
        name="item-update",
    ),
    path(
        "items/<path:item_key>/remove/",
        views.pos_remove_item_view,
        name="item-remove",
    ),
    path(
        "clear/",
        views.pos_clear_cart_view,
        name="clear",
    ),
    path(
    "checkout/",
    views.pos_checkout_view,
    name="checkout",
),
    path(
        "orders/<uuid:order_id>/success/",
        views.pos_order_success_view,
        name="success",
    ),
]