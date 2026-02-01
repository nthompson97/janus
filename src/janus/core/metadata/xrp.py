from typing import final

from ._base import Coin


@final
class XRP(Coin):
    name = "XRP"
    aliases = [
        "XRP",
        "Ripple",
    ]
