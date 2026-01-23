from typing import final

from ._base import Coin


@final
class USDC(Coin):
    name = "USDC"
    aliases = [
        "USDC",
        "USD Coin",
    ]
