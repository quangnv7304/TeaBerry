from django.contrib import admin

from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "phone",
        "is_accepting_orders",
        "is_active",
    )

    list_filter = (
        "is_accepting_orders",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
        "phone",
    )
    
    