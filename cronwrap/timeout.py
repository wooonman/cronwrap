"""Timeout configuration and enforcement utilities."""
from dataclasses import dataclass, field
from typing import Optional
import signal
import contextlib


@dataclass
class TimeoutConfig:
    seconds: Optional[int] = None
    kill_on_expire: bool = True
    message: str = "Command timed out"

    @property
    def enabled(self) -> bool:
        return self.seconds is not None and self.seconds > 0


def from_dict(d: dict) -> TimeoutConfig:
    return TimeoutConfig(
        seconds=d.get("seconds"),
        kill_on_expire=d.get("kill_on_expire", True),
        message=d.get("message", "Command timed out"),
    )


class TimeoutExpired(Exception):
    def __init__(self, seconds: int, message: str = "Command timed out"):
        self.seconds = seconds
        super().__init__(f"{message} after {seconds}s")


@contextlib.contextmanager
def timeout_guard(config: TimeoutConfig):
    """Context manager that raises TimeoutExpired if block exceeds config.seconds."""
    if not config.enabled:
        yield
        return

    def _handler(signum, frame):
        raise TimeoutExpired(config.seconds, config.message)

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(config.seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def describe_timeout(config: TimeoutConfig) -> str:
    if not config.enabled:
        return "no timeout"
    return f"timeout={config.seconds}s (kill={config.kill_on_expire})"
