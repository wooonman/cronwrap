"""Backoff strategies for retry delays."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

BackoffStrategy = Literal["constant", "linear", "exponential", "jitter"]


@dataclass
class BackoffConfig:
    strategy: BackoffStrategy = "constant"
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter_range: float = 0.5

    @classmethod
    def from_dict(cls, data: dict) -> "BackoffConfig":
        return cls(
            strategy=data.get("strategy", "constant"),
            base_delay=float(data.get("base_delay", 1.0)),
            max_delay=float(data.get("max_delay", 60.0)),
            multiplier=float(data.get("multiplier", 2.0)),
            jitter_range=float(data.get("jitter_range", 0.5)),
        )

    def enabled(self) -> bool:
        return self.base_delay > 0

    def delay_for(self, attempt: int) -> float:
        """Return delay in seconds for the given attempt number (1-based)."""
        if attempt < 1:
            attempt = 1

        if self.strategy == "constant":
            delay = self.base_delay
        elif self.strategy == "linear":
            delay = self.base_delay * attempt
        elif self.strategy == "exponential":
            delay = self.base_delay * (self.multiplier ** (attempt - 1))
        elif self.strategy == "jitter":
            base = self.base_delay * (self.multiplier ** (attempt - 1))
            jitter = random.uniform(-self.jitter_range, self.jitter_range) * base
            delay = base + jitter
        else:
            delay = self.base_delay

        return max(0.0, min(delay, self.max_delay))

    def describe(self) -> str:
        return (
            f"strategy={self.strategy} base={self.base_delay}s "
            f"max={self.max_delay}s multiplier={self.multiplier}"
        )
