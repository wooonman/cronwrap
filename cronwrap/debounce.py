"""Debounce support — suppress repeated runs within a cooldown window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DebounceConfig:
    job_id: str
    cooldown_seconds: int = 0
    state_dir: str = "/tmp/cronwrap/debounce"

    def enabled(self) -> bool:
        return self.cooldown_seconds > 0

    @classmethod
    def from_dict(cls, data: dict) -> "DebounceConfig":
        return cls(
            job_id=data.get("job_id", "default"),
            cooldown_seconds=int(data.get("cooldown_seconds", 0)),
            state_dir=data.get("state_dir", "/tmp/cronwrap/debounce"),
        )


def _state_path(config: DebounceConfig) -> Path:
    return Path(config.state_dir) / f"{config.job_id}.json"


def _read_last_run(config: DebounceConfig) -> Optional[float]:
    path = _state_path(config)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return float(data.get("last_run", 0))
    except (json.JSONDecodeError, ValueError):
        return None


def _write_last_run(config: DebounceConfig, ts: float) -> None:
    path = _state_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_run": ts}))


def check_debounce(config: DebounceConfig) -> tuple[bool, str]:
    """Return (allowed, reason). Writes timestamp only when allowed."""
    if not config.enabled():
        return True, "debounce disabled"

    last = _read_last_run(config)
    now = time.time()

    if last is not None:
        elapsed = now - last
        if elapsed < config.cooldown_seconds:
            remaining = config.cooldown_seconds - elapsed
            return False, (
                f"debounced: {remaining:.1f}s remaining in "
                f"{config.cooldown_seconds}s cooldown"
            )

    _write_last_run(config, now)
    return True, "allowed"


def reset_debounce(config: DebounceConfig) -> bool:
    path = _state_path(config)
    if path.exists():
        path.unlink()
        return True
    return False
