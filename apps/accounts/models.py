from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = "CUSTOMER", "Khách hàng"
    STAFF = "STAFF", "Nhân viên"
    MANAGER = "MANAGER", "Quản lý"
    ADMIN = "ADMIN", "Quản trị viên"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Người dùng phải có địa chỉ email.")

        email = self.normalize_email(email)

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", UserRole.CUSTOMER)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser phải có is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser phải có is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )

    phone = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Số điện thoại",
    )

    full_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Họ và tên",
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        verbose_name="Vai trò",
    )
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="Khách hàng",
    )

    recipient_name = models.CharField(
        max_length=150,
        verbose_name="Tên người nhận",
    )

    recipient_phone = models.CharField(
        max_length=20,
        verbose_name="Số điện thoại",
    )

    address_line = models.CharField(
        max_length=255,
        verbose_name="Địa chỉ chi tiết",
    )

    ward = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Phường/Xã",
    )

    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Quận/Huyện",
    )

    province = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tỉnh/Thành phố",
    )

    label = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Nhãn địa chỉ",
        help_text="Ví dụ: Nhà, Công ty",
    )

    delivery_note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú giao hàng",
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name="Địa chỉ mặc định",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang sử dụng",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-is_default",
            "-updated_at",
        )
        verbose_name = "Địa chỉ"
        verbose_name_plural = "Địa chỉ"

    def __str__(self) -> str:
        return (
            f"{self.recipient_name} - "
            f"{self.address_line}"
        )

    @property
    def full_address(self) -> str:
        parts = [
            self.address_line,
            self.ward,
            self.district,
            self.province,
        ]

        return ", ".join(
            part.strip()
            for part in parts
            if part and part.strip()
        )

