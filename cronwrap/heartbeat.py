"""Heartbeat module — periodically pings a URL to signal the job is alive."""
from __future__ import annotations

import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HeartbeatConfig:
    url: str = ""
    interval_seconds: float = 0.0  # 0 = ping once (at start/end only)
    timeout_seconds: float = 5.0
    headers: dict = field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    @classmethod
    def from_dict(cls, data: dict) -> "HeartbeatConfig":
        return cls(
            url=data.get("url", ""),
            interval_seconds=float(data.get("interval_seconds", 0.0)),
            timeout_seconds=float(data.get("timeout_seconds", 5.0)),
            headers=data.get("headers", {}),
        )


def ping(config: HeartbeatConfig, suffix: str = "") -> bool:
    """Send a single GET ping to the heartbeat URL. Returns True on success."""
    if not config.enabled:
        return False
    url = config.url.rstrip("/")
    if suffix:
        url = f"{url}/{suffix.lstrip('/')}"
    req = urllib.request.Request(url, headers=config.headers)
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_seconds):
            return True
    except (urllib.error.URLError, OSError):
        return False


def ping_start(config: HeartbeatConfig) -> bool:
    return ping(config, suffix="start")


def ping_finish(config: HeartbeatConfig, success: bool = True) -> bool:
    suffix = "finish" if success else "fail"
    return ping(config, suffix=suffix)


def ping_loop(config: HeartbeatConfig, stop_event) -> None:
    """Ping in a loop until stop_event is set. Intended to run in a thread."""
    while not stop_event.is_set():
        ping(config)
        stop_event.wait(timeout=config.interval_seconds or 30.0)
