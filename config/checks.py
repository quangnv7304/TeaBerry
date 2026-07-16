from django.conf import settings
from django.core.checks import Error, Warning, register


@register()
def check_teaberry_settings(
    app_configs,
    **kwargs,
):
    errors = []

    if not settings.DEBUG:
        if settings.SECRET_KEY.startswith(
            "django-insecure-"
        ):
            errors.append(
                Error(
                    "SECRET_KEY production chưa an toàn.",
                    hint=(
                        "Đặt DJANGO_SECRET_KEY trong "
                        "biến môi trường."
                    ),
                    id="teaberry.E001",
                )
            )

        if not settings.ALLOWED_HOSTS:
            errors.append(
                Error(
                    "ALLOWED_HOSTS đang để trống.",
                    hint=(
                        "Khai báo domain hoặc hostname "
                        "của website."
                    ),
                    id="teaberry.E002",
                )
            )

        if not settings.CSRF_TRUSTED_ORIGINS:
            errors.append(
                Warning(
                    "CSRF_TRUSTED_ORIGINS đang để trống.",
                    hint="Thêm HTTPS domain production.",
                    id="teaberry.W001",
                )
            )

    required_bank_settings = {
        "TEABERRY_BANK_CODE": settings.TEABERRY_BANK_CODE,
        "TEABERRY_BANK_ACCOUNT": settings.TEABERRY_BANK_ACCOUNT,
        "TEABERRY_BANK_HOLDER": settings.TEABERRY_BANK_HOLDER,
    }

    for name, value in required_bank_settings.items():
        if not value:
            errors.append(
                Warning(
                    f"{name} chưa được cấu hình.",
                    hint=(
                        "Kiểm tra file .env hoặc "
                        "biến môi trường."
                    ),
                    id="teaberry.W002",
                )
            )

    return errors
