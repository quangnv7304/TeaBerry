from django.core.exceptions import PermissionDenied

from apps.accounts.models import UserRole


KITCHEN_ROLES = {
    UserRole.STAFF,
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_kitchen_access(user) -> None:
    if not user.is_authenticated:
        raise PermissionDenied

    if user.is_superuser:
        return

    if user.role not in KITCHEN_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền truy cập màn hình pha chế."
        )