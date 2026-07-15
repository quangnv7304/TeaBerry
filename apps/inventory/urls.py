from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path(
        "",
        views.inventory_dashboard_view,
        name="dashboard",
    ),
    path(
        "ingredients/<int:ingredient_id>/import/",
        views.import_stock_view,
        name="import-stock",
    ),
]