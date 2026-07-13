from django.contrib import admin

from .models import Address, User

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_name",
        "recipient_phone",
        "user",
        "province",
        "district",
        "is_default",
        "is_active",
    )

    list_filter = (
        "is_default",
        "is_active",
        "province",
        "district",
    )

    search_fields = (
        "recipient_name",
        "recipient_phone",
        "address_line",
        "user__email",
    )

    list_select_related = ("user",)
