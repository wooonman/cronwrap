"""Jitter support for retry delays — adds randomness to avoid thundering herd."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

JitterStrategy = Literal["none", "full", "equal", "decorrelated"]


@dataclass
class JitterConfig:
    strategy: JitterStrategy = "none"
    max_ms: int = 1000  # cap on jitter added, in milliseconds
    seed: int | None = None  # optional seed for reproducibility in tests

    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    @classmethod
    def from_dict(cls, data: dict) -> "JitterConfig":
        return cls(
            strategy=data.get("strategy", "none"),
            max_ms=int(data.get("max_ms", 1000)),
            seed=data.get("seed"),
        )

    def enabled(self) -> bool:
        return self.strategy != "none"

    def apply(self, base_delay: float, attempt: int = 1) -> float:
        """Return base_delay adjusted by jitter (in seconds)."""
        if not self.enabled():
            return base_delay

        cap = self.max_ms / 1000.0

        if self.strategy == "full":
            # Uniform jitter between 0 and base_delay
            return self._rng.uniform(0, max(base_delay, cap))

        if self.strategy == "equal":
            # Half base + half random
            half = base_delay / 2.0
            return half + self._rng.uniform(0, min(half, cap))

        if self.strategy == "decorrelated":
            # AWS decorrelated jitter: random between base and 3 * previous
            # We approximate using attempt to scale
            upper = min(base_delay * 3, base_delay + cap)
            return self._rng.uniform(base_delay, upper)

        return base_delay

    def describe(self) -> str:
        if not self.enabled():
            return "jitter disabled"
        return f"jitter strategy={self.strategy} max_ms={self.max_ms}"
