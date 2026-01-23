from ._base import Coin
from typing import final


@final
class BTC(Coin):
    name = "BTC"
    aliases = [
        "BTC",
        "Bitcoin",
    ]
