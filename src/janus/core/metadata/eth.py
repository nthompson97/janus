from ._base import Coin


class Ethereum(Coin):
    name: str = "ETH"
    aliases: list[str] = [
        "ETH",
        "ETH-USC",
        "Ethereum",
    ]
