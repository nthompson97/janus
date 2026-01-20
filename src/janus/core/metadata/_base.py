from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Coin:
    name: ClassVar[str]
    aliases: ClassVar[list[str]] = []  # field(default_factory=lambda: [])

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
