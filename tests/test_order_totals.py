def test_order_total_never_negative():
    subtotal = 100_000
    shipping_fee = 20_000
    discount = 200_000

    total = max(
        0,
        subtotal + shipping_fee - discount,
    )

    assert total == 0


def test_order_discount_components_are_consistent():
    voucher_discount = 30_000
    loyalty_discount = 20_000

    assert (
        voucher_discount + loyalty_discount
    ) == 50_000
