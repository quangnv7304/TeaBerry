from django.views.generic import DetailView, ListView

from .models import Product, ProductStatus


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        return (
            Product.objects.filter(
                is_active=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            )
            .select_related("store", "category")
            .order_by("-is_featured", "name")
        )


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(
                is_active=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            )
            .select_related(
                "store",
                "category",
            )
            .prefetch_related(
                "images",
                "variants",
                "product_toppings__topping",
                "product_options__option_choice",
            )
        )
