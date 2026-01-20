from ._base import Coin


class Bitcoin(Coin):
    name: str = "BTC"
    aliases: list[str] = [
        "BTC",
        "BTC-USC",
        "Bitcoin",
    ]
