import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_orderstatushistory_alter_orderitem_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="orderitem",
            options={
                "ordering": ("id",),
                "verbose_name": "Sản phẩm trong đơn",
                "verbose_name_plural": "Sản phẩm trong đơn",
            },
        ),
        migrations.AlterModelOptions(
            name="orderstatushistory",
            options={
                "ordering": ("created_at",),
                "verbose_name": "Lịch sử trạng thái đơn",
                "verbose_name_plural": "Lịch sử trạng thái đơn",
            },
        ),
        migrations.RemoveIndex(
            model_name="orderitem",
            name="orders_orde_order_i_4ba133_idx",
        ),
        migrations.AddField(
            model_name="orderstatushistory",
            name="changed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_status_changes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Người thực hiện",
            ),
        ),
        migrations.AddField(
            model_name="orderstatushistory",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name="Thời gian",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderstatushistory",
            name="new_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Chờ xác nhận"),
                    ("CONFIRMED", "Đã xác nhận"),
                    ("PREPARING", "Đang pha chế"),
                    ("READY", "Sẵn sàng giao"),
                    ("DELIVERING", "Đang giao"),
                    ("COMPLETED", "Hoàn thành"),
                    ("CANCELLED", "Đã hủy"),
                ],
                default="PENDING",
                max_length=30,
                verbose_name="Trạng thái mới",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderstatushistory",
            name="note",
            field=models.CharField(blank=True, max_length=255, verbose_name="Ghi chú"),
        ),
        migrations.AddField(
            model_name="orderstatushistory",
            name="old_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("PENDING", "Chờ xác nhận"),
                    ("CONFIRMED", "Đã xác nhận"),
                    ("PREPARING", "Đang pha chế"),
                    ("READY", "Sẵn sàng giao"),
                    ("DELIVERING", "Đang giao"),
                    ("COMPLETED", "Hoàn thành"),
                    ("CANCELLED", "Đã hủy"),
                ],
                max_length=30,
                verbose_name="Trạng thái cũ",
            ),
        ),
        migrations.AddIndex(
            model_name="orderstatushistory",
            index=models.Index(fields=["order", "created_at"], name="orders_orde_order_i_1de1d7_idx"),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity__gt", 0)),
                name="order_item_quantity_gt_0",
            ),
        ),
        migrations.AddConstraint(
            model_name="orderitem",
            constraint=models.CheckConstraint(
                condition=models.Q(("line_total__gte", 0)),
                name="order_item_line_total_gte_0",
            ),
        ),
        migrations.RemoveField(model_name="orderitem", name="changed_by"),
        migrations.RemoveField(model_name="orderitem", name="created_at"),
        migrations.RemoveField(model_name="orderitem", name="new_status"),
        migrations.RemoveField(model_name="orderitem", name="old_status"),
    ]
