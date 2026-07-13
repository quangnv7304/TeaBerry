from django.db import transaction

from .models import Address, User


@transaction.atomic
def save_address(
    *,
    user: User,
    form,
    address: Address | None = None,
) -> Address:
    if address is None:
        address = form.save(commit=False)
        address.user = user
    else:
        address = form.save(commit=False)

    if address.is_default:
        (
            Address.objects
            .filter(
                user=user,
                is_default=True,
            )
            .exclude(pk=address.pk)
            .update(is_default=False)
        )

    address.save()

    if not Address.objects.filter(
        user=user,
        is_active=True,
        is_default=True,
    ).exists():
        address.is_default = True
        address.save(
            update_fields=[
                "is_default",
                "updated_at",
            ]
        )

    return address


@transaction.atomic
def set_default_address(
    *,
    user: User,
    address: Address,
) -> Address:
    Address.objects.filter(
        user=user,
        is_default=True,
    ).exclude(pk=address.pk).update(
        is_default=False
    )

    address.is_default = True
    address.is_active = True
    address.save(
        update_fields=[
            "is_default",
            "is_active",
            "updated_at",
        ]
    )

    return address