import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        ("stores", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("order_code", models.CharField(max_length=20, unique=True)),
                ("customer_name", models.CharField(max_length=150)),
                ("customer_phone", models.CharField(max_length=20)),
                ("shipping_address", models.TextField()),
                ("note", models.TextField(blank=True)),
                ("shipping_fee", models.PositiveIntegerField(default=0)),
                ("discount", models.PositiveIntegerField(default=0)),
                ("subtotal", models.PositiveIntegerField(default=0)),
                ("total", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(default="PENDING", max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("customer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="orders", to=settings.AUTH_USER_MODEL)),
                ("store", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="stores.store")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=200)),
                ("variant_name", models.CharField(blank=True, max_length=100)),
                ("sugar", models.CharField(blank=True, max_length=50)),
                ("ice", models.CharField(blank=True, max_length=50)),
                ("toppings", models.JSONField(blank=True, default=list)),
                ("unit_price", models.PositiveIntegerField()),
                ("quantity", models.PositiveIntegerField()),
                ("line_total", models.PositiveIntegerField()),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="order_items", to="catalog.product")),
            ],
            options={"ordering": ("id",)},
        ),
    ]
