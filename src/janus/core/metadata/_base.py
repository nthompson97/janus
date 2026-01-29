from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, override


class _CoinMeta(type):
    """Metaclass for Coin that enables operator overloading on classes.

    This allows syntax like:
        BTC / USDC  -> Spot(Bitcoin, USDC)
        BTC - USDC  -> Perpetual(Bitcoin, USDC)
    """

    def __truediv__(cls: type[Coin], other: type[Coin]) -> Spot:
        return Spot(base=cls, quote=other)

    def __sub__(cls: type[Coin], other: type[Coin]) -> Perpetual:
        return Perpetual(base=cls, quote=other)


@dataclass(frozen=True, eq=False)
class Coin(metaclass=_CoinMeta):
    name: ClassVar[str]
    aliases: ClassVar[list[str]] = []

    _registry: ClassVar[dict[str, type["Coin"]]] = {}

    def __init_subclass__(cls: type["Coin"]) -> None:
        # Maintain the _registry class variable, mapping each coin to it's
        # associated aliases
        super.__init_subclass__()

        keys: set[str] = {cls.name, *cls.aliases}

        for k in keys:
            if k.lower() in Coin._registry:
                raise ValueError(f"Duplicate coin key: {k}")

            Coin._registry[k.lower()] = cls

    @classmethod
    def from_name(cls, name: str) -> type["Coin"]:
        try:
            return cls._registry[name.lower()]

        except KeyError:
            raise KeyError(
                f"Unkown coin name or alias: {name}. Known keys: {cls._registry}"
            )

    @override
    def __str__(self) -> str:
        return self.name

    @override
    def __repr__(self) -> str:
        return f"Coin({self.name})"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coin):
            return False

        return self.name == other.name

    @override
    def __hash__(self) -> int:
        return hash(self.name)


@dataclass(frozen=True, eq=False)
class Spot:
    """A spot (cross) asset representing a pair of coins.

    Represents a spot trading pair like BTC/USDC. Can be constructed
    using the division operator on Coin instances:

        >>> BTC / USDC
        Spot(base=Bitcoin, quote=USDC)
    """

    base: type[Coin]
    quote: type[Coin]

    @override
    def __str__(self) -> str:
        return f"{self.base.name}/{self.quote.name}"

    @override
    def __repr__(self) -> str:
        return f"Spot({self.base.name}, {self.quote.name})"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Spot):
            return False

        return self.base == other.base and self.quote == other.quote

    @override
    def __hash__(self) -> int:
        return hash((self.base.name, self.quote.name))


@dataclass(frozen=True, eq=False)
class Perpetual:
    """A perpetual futures asset representing a pair of coins.

    Represents a perpetual futures contract like BTC-USDC. Can be constructed
    using the subtraction operator on Coin instances:

        >>> BTC - USDC
        Perpetual(base=Bitcoin, quote=USDC)
    """

    base: type[Coin]
    quote: type[Coin]

    @override
    def __str__(self) -> str:
        return f"{self.base.name}-{self.quote.name}"

    @override
    def __repr__(self) -> str:
        return f"Perpetual({self.base.name}, {self.quote.name})"

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Perpetual):
            return False

        return self.base == other.base and self.quote == other.quote

    @override
    def __hash__(self) -> int:
        return hash((self.base.name, self.quote.name))
