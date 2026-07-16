from django.core.exceptions import PermissionDenied

from apps.accounts.models import UserRole


REPORT_ROLES = {
    UserRole.MANAGER,
    UserRole.ADMIN,
}


def ensure_report_access(user) -> None:
    if user.is_superuser:
        return

    if user.role not in REPORT_ROLES:
        raise PermissionDenied(
            "Bạn không có quyền xem báo cáo."
        )