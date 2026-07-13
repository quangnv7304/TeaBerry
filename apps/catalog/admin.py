from django.contrib import admin

from .models import (
    Category,
    OptionChoice,
    Product,
    ProductImage,
    ProductOption,
    ProductTopping,
    ProductVariant,
    Topping,
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 1
    autocomplete_fields = ("option_choice",)

class ProductToppingInline(admin.TabularInline):
    model = ProductTopping
    extra = 1
    autocomplete_fields = ("topping",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store",
        "display_order",
        "is_active",
    )

    list_filter = (
        "store",
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store",
        "category",
        "base_price",
        "status",
        "is_featured",
        "is_active",
    )

    list_filter = (
        "store",
        "category",
        "status",
        "is_featured",
        "is_active",
    )

    search_fields = (
        "name",
        "slug",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    inlines = (
        ProductImageInline,
        ProductVariantInline,
        ProductOptionInline,
        ProductToppingInline,
    )


@admin.register(Topping)
class ToppingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "store",
        "price",
        "is_available",
        "display_order",
    )

    list_filter = (
        "store",
        "is_available",
    )

    search_fields = ("name",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "name",
        "price",
        "is_default",
        "is_available",
    )

    list_filter = (
        "is_default",
        "is_available",
    )

    search_fields = (
        "product__name",
        "name",
    )
@admin.register(OptionChoice)
class OptionChoiceAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "option_type",
        "code",
        "display_order",
        "is_active",
    )

    list_filter = (
        "option_type",
        "is_active",
    )

    search_fields = (
        "label",
        "code",
    )

    ordering = (
        "option_type",
        "display_order",
    )