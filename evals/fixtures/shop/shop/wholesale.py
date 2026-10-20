def shipping_fee_won(subtotal_won: int) -> int:
    if type(subtotal_won) is not int or subtotal_won < 0:
        raise ValueError("invalid subtotal")
    return 0 if subtotal_won >= 100_000 else 5_000
