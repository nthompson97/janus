from ._base import Coin
from typing import final


@final
class SOL(Coin):
    name = "SOL"
    aliases = [
        "SOL",
        "Solana",
    ]
