from django.views.generic import DetailView, ListView

from .models import Category, Product, ProductStatus


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Product.objects.filter(
                is_active=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            )
            .select_related("store", "category")
            .order_by("-is_featured", "name")
        )

        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        minimum_price = self.request.GET.get("min_price", "").strip()
        maximum_price = self.request.GET.get("max_price", "").strip()
        sort = self.request.GET.get("sort", "featured")

        if query:
            queryset = queryset.filter(name__icontains=query)
        if category:
            queryset = queryset.filter(category__slug=category)
        if minimum_price.isdigit():
            queryset = queryset.filter(base_price__gte=int(minimum_price))
        if maximum_price.isdigit():
            queryset = queryset.filter(base_price__lte=int(maximum_price))

        ordering = {
            "featured": ("-is_featured", "name"),
            "newest": ("-created_at",),
            "price_low": ("base_price", "name"),
            "price_high": ("-base_price", "name"),
            "popular": ("-is_featured", "-created_at"),
        }
        return queryset.order_by(*ordering.get(sort, ordering["featured"]))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.filter(
            is_active=True,
            store__is_active=True,
        ).order_by("display_order", "name")
        context["featured_products"] = list(
            Product.objects.filter(
                is_active=True,
                is_featured=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            ).select_related("category")[:4]
        )
        context["current_query"] = self.request.GET.get("q", "")
        context["current_category"] = self.request.GET.get("category", "")
        context["current_sort"] = self.request.GET.get("sort", "featured")
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["related_products"] = (
            Product.objects.filter(
                category=self.object.category,
                is_active=True,
                status=ProductStatus.ACTIVE,
                store__is_active=True,
            )
            .exclude(pk=self.object.pk)
            .select_related("category")[:4]
        )
        return context
