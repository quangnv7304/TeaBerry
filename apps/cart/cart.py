from decimal import Decimal

from apps.catalog.models import (
    OptionChoice,
    Product,
    ProductOption,
    ProductTopping,
    ProductVariant,
)


class SessionCart:
    SESSION_KEY = "teaberry_cart"

    def __init__(self, request):
        self.session = request.session
        self.cart = self.session.get(self.SESSION_KEY, {})

    def save(self) -> None:
        self.session[self.SESSION_KEY] = self.cart
        self.session.modified = True

    def add(
        self,
        *,
        product: Product,
        variant: ProductVariant | None,
        sugar_choice: OptionChoice | None,
        ice_choice: OptionChoice | None,
        toppings: list[ProductTopping],
        quantity: int,
        note: str = "",
    ) -> None:
        topping_ids = sorted(
            str(item.topping_id)
            for item in toppings
        )

        configuration_key = ":".join(
            [
                str(product.id),
                str(variant.id if variant else ""),
                str(sugar_choice.id if sugar_choice else ""),
                str(ice_choice.id if ice_choice else ""),
                ",".join(topping_ids),
                note.strip().lower(),
            ]
        )

        product_price = (
            variant.price
            if variant is not None
            else product.base_price
        )

        topping_total = sum(
            item.topping.price
            for item in toppings
        )

        if configuration_key not in self.cart:
            self.cart[configuration_key] = {
                "product_id": product.id,
                "product_name": product.name,
                "product_slug": product.slug,
                "variant_id": variant.id if variant else None,
                "variant_name": variant.name if variant else "",
                "sugar_choice_id": (
                    sugar_choice.id if sugar_choice else None
                ),
                "sugar_label": (
                    sugar_choice.label if sugar_choice else ""
                ),
                "ice_choice_id": (
                    ice_choice.id if ice_choice else None
                ),
                "ice_label": (
                    ice_choice.label if ice_choice else ""
                ),
                "toppings": [
                    {
                        "id": item.topping.id,
                        "name": item.topping.name,
                        "price": item.topping.price,
                    }
                    for item in toppings
                ],
                "product_price": product_price,
                "topping_total": topping_total,
                "quantity": 0,
                "note": note.strip(),
            }

        self.cart[configuration_key]["quantity"] += quantity
        self.save()

    def remove(self, *, key: str) -> None:
        if key in self.cart:
            del self.cart[key]
            self.save()

    def update_quantity(
        self,
        *,
        key: str,
        quantity: int,
    ) -> None:
        if key not in self.cart:
            return

        if quantity <= 0:
            self.remove(key=key)
            return

        self.cart[key]["quantity"] = quantity
        self.save()

    def clear(self) -> None:
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True

    def __iter__(self):
        for key, item in self.cart.items():
            product_price = int(item["product_price"])
            topping_total = int(item["topping_total"])
            quantity = int(item["quantity"])

            item_copy = item.copy()
            item_copy["key"] = key
            item_copy["unit_total"] = (
                product_price + topping_total
            )
            item_copy["line_total"] = (
                product_price + topping_total
            ) * quantity

            yield item_copy

    def __len__(self) -> int:
        return sum(
            int(item["quantity"])
            for item in self.cart.values()
        )

    def get_total_price(self) -> int:
        return sum(
            (
                int(item["product_price"])
                + int(item["topping_total"])
            )
            * int(item["quantity"])
            for item in self.cart.values()
        )