from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("loyalty", "0002_alter_loyaltytransaction_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="loyaltytransaction",
            name="unique_order_loyalty_earn",
        ),
        migrations.RenameField(
            model_name="loyaltyaccount",
            old_name="total_points",
            new_name="available_points",
        ),
        migrations.AddField(
            model_name="loyaltytransaction",
            name="balance_after",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name="Số dư sau giao dịch",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="loyaltytransaction",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_loyalty_transactions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Người thực hiện",
            ),
        ),
        migrations.AlterModelOptions(
            name="loyaltyaccount",
            options={
                "verbose_name": "Tài khoản điểm thưởng",
                "verbose_name_plural": "Tài khoản điểm thưởng",
            },
        ),
        migrations.AlterModelOptions(
            name="loyaltytransaction",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Giao dịch điểm thưởng",
                "verbose_name_plural": "Giao dịch điểm thưởng",
            },
        ),
        migrations.AlterField(
            model_name="loyaltyaccount",
            name="available_points",
            field=models.PositiveIntegerField(default=0, verbose_name="Điểm khả dụng"),
        ),
        migrations.AlterField(
            model_name="loyaltyaccount",
            name="customer",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="loyalty_account",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Khách hàng",
            ),
        ),
        migrations.AlterField(
            model_name="loyaltyaccount",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Đang hoạt động"),
        ),
        migrations.AlterField(
            model_name="loyaltyaccount",
            name="lifetime_points",
            field=models.PositiveIntegerField(default=0, verbose_name="Tổng điểm tích lũy"),
        ),
        migrations.AlterField(
            model_name="loyaltyaccount",
            name="tier",
            field=models.CharField(
                choices=[
                    ("MEMBER", "Thành viên"), ("SILVER", "Bạc"),
                    ("GOLD", "Vàng"), ("PLATINUM", "Bạch kim"),
                ],
                default="MEMBER",
                max_length=20,
                verbose_name="Hạng thành viên",
            ),
        ),
        migrations.AlterField(
            model_name="loyaltytransaction",
            name="account",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to="loyalty.loyaltyaccount",
                verbose_name="Tài khoản điểm",
            ),
        ),
        migrations.AlterField(
            model_name="loyaltytransaction",
            name="note",
            field=models.CharField(blank=True, max_length=255, verbose_name="Ghi chú"),
        ),
        migrations.AlterField(
            model_name="loyaltytransaction",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="loyalty_transactions",
                to="orders.order",
                verbose_name="Đơn hàng",
            ),
        ),
        migrations.AlterField(
            model_name="loyaltytransaction",
            name="points",
            field=models.IntegerField(
                help_text="Số dương khi cộng điểm, số âm khi trừ điểm.",
                verbose_name="Số điểm thay đổi",
            ),
        ),
        migrations.AlterField(
            model_name="loyaltytransaction",
            name="transaction_type",
            field=models.CharField(
                choices=[
                    ("EARN", "Tích điểm"), ("REDEEM", "Đổi điểm"),
                    ("ADJUST", "Điều chỉnh"), ("EXPIRE", "Điểm hết hạn"),
                ],
                max_length=20,
                verbose_name="Loại giao dịch",
            ),
        ),
        migrations.AddConstraint(
            model_name="loyaltytransaction",
            constraint=models.UniqueConstraint(
                condition=models.Q(order__isnull=False, transaction_type="EARN"),
                fields=("account", "order", "transaction_type"),
                name="unique_loyalty_earn_per_order",
            ),
        ),
        migrations.AddConstraint(
            model_name="loyaltytransaction",
            constraint=models.CheckConstraint(
                condition=~models.Q(points=0),
                name="loyalty_transaction_points_not_zero",
            ),
        ),
    ]
