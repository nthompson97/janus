from ._base import Coin
from typing import final


@final
class ETH(Coin):
    name = "ETH"
    aliases = [
        "ETH",
        "Ethereum",
    ]
