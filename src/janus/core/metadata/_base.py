from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Coin:
    name: str
    aliases: list[str] = field(default_factory=lambda: [])
