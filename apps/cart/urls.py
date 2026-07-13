from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path(
        "",
        views.cart_detail_view,
        name="detail",
    ),
    path(
        "add/",
        views.add_to_cart_view,
        name="add",
    ),
    path(
        "items/<path:key>/update/",
        views.update_cart_item_view,
        name="item-update",
    ),
    path(
        "items/<path:key>/remove/",
        views.remove_cart_item_view,
        name="item-remove",
    ),
]