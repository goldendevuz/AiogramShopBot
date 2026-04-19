import config
from enums.currency import Currency


def fmt(amount) -> str:
    amount = float(amount or 0)
    if config.CURRENCY == Currency.UZS:
        return f"{amount:,.0f}".replace(",", " ")
    return f"{amount:,.2f}"

