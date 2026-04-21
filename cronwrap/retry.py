"""Retry policy configuration and execution logic."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class RetryPolicy:
    max_attempts: int = 1
    delay: float = 0.0
    backoff: float = 1.0
    retry_on_exit_codes: list[int] = field(default_factory=list)
    retry_on_timeout: bool = False

    @property
    def enabled(self) -> bool:
        return self.max_attempts > 1

    @classmethod
    def from_dict(cls, data: dict) -> "RetryPolicy":
        return cls(
            max_attempts=int(data.get("max_attempts", 1)),
            delay=float(data.get("delay", 0.0)),
            backoff=float(data.get("backoff", 1.0)),
            retry_on_exit_codes=list(data.get("retry_on_exit_codes", [])),
            retry_on_timeout=bool(data.get("retry_on_timeout", False)),
        )

    def should_retry(self, exit_code: int, timed_out: bool = False) -> bool:
        if timed_out:
            return self.retry_on_timeout
        if self.retry_on_exit_codes:
            return exit_code in self.retry_on_exit_codes
        return exit_code != 0

    def delay_for(self, attempt: int) -> float:
        """Return sleep duration before the given attempt (0-indexed)."""
        if attempt == 0 or self.delay <= 0:
            return 0.0
        return self.delay * (self.backoff ** (attempt - 1))


@dataclass
class RetryState:
    attempt: int = 0
    total_attempts: int = 0
    gave_up: bool = False
    last_exit_code: int = 0


def run_with_retry(
    policy: RetryPolicy,
    fn: Callable[[], tuple[int, bool]],
    sleep_fn: Optional[Callable[[float], None]] = None,
) -> RetryState:
    """Run *fn* up to policy.max_attempts times.

    *fn* must return (exit_code, timed_out).
    Returns a RetryState describing the outcome.
    """
    _sleep = sleep_fn if sleep_fn is not None else time.sleep
    state = RetryState()

    for attempt in range(policy.max_attempts):
        wait = policy.delay_for(attempt)
        if wait > 0:
            _sleep(wait)

        exit_code, timed_out = fn()
        state.attempt = attempt
        state.total_attempts = attempt + 1
        state.last_exit_code = exit_code

        if not policy.should_retry(exit_code, timed_out):
            state.gave_up = False
            return state

    state.gave_up = True
    return state
