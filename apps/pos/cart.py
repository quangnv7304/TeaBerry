from apps.catalog.models import (
    OptionChoice,
    Product,
    ProductTopping,
    ProductVariant,
)


class PosCart:
    SESSION_KEY = "teaberry_pos_cart"

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
        quantity: int = 1,
        note: str = "",
    ) -> None:
        topping_ids = sorted(
            str(relation.topping_id)
            for relation in toppings
        )

        item_key = ":".join(
            [
                str(product.id),
                str(variant.id if variant else ""),
                str(sugar_choice.id if sugar_choice else ""),
                str(ice_choice.id if ice_choice else ""),
                ",".join(topping_ids),
                note.strip().lower(),
            ]
        )

        unit_price = int(
            variant.price
            if variant is not None
            else product.base_price
        )

        topping_total = sum(
            int(relation.topping.price)
            for relation in toppings
        )

        if item_key not in self.cart:
            self.cart[item_key] = {
                "product_id": product.id,
                "product_name": product.name,
                "product_slug": product.slug,
                "variant_id": (
                    variant.id if variant else None
                ),
                "variant_name": (
                    variant.name if variant else ""
                ),
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
                        "id": relation.topping.id,
                        "name": relation.topping.name,
                        "price": int(relation.topping.price),
                    }
                    for relation in toppings
                ],
                "unit_price": unit_price,
                "topping_total": topping_total,
                "quantity": 0,
                "note": note.strip(),
            }

        self.cart[item_key]["quantity"] += quantity
        self.save()

    def update_quantity(
        self,
        *,
        item_key: str,
        quantity: int,
    ) -> None:
        if item_key not in self.cart:
            return

        if quantity <= 0:
            self.remove(item_key=item_key)
            return

        self.cart[item_key]["quantity"] = quantity
        self.save()

    def remove(self, *, item_key: str) -> None:
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def clear(self) -> None:
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True

    def __iter__(self):
        for item_key, item in self.cart.items():
            item_copy = item.copy()
            item_copy["item_key"] = item_key

            item_copy["unit_total"] = (
                int(item["unit_price"])
                + int(item["topping_total"])
            )

            item_copy["line_total"] = (
                item_copy["unit_total"]
                * int(item["quantity"])
            )

            yield item_copy

    def __len__(self) -> int:
        return sum(
            int(item["quantity"])
            for item in self.cart.values()
        )

    def get_total(self) -> int:
        return sum(
            (
                int(item["unit_price"])
                + int(item["topping_total"])
            )
            * int(item["quantity"])
            for item in self.cart.values()
        )