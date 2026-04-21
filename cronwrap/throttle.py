"""Throttle support: skip a run if the last successful run was too recent."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ThrottleConfig:
    min_interval_seconds: int = 0  # 0 means disabled
    state_dir: str = "/tmp/cronwrap/throttle"

    @property
    def enabled(self) -> bool:
        return self.min_interval_seconds > 0

    @classmethod
    def from_dict(cls, data: dict) -> "ThrottleConfig":
        return cls(
            min_interval_seconds=int(data.get("min_interval_seconds", 0)),
            state_dir=data.get("state_dir", "/tmp/cronwrap/throttle"),
        )


def _state_path(job_name: str, state_dir: str) -> Path:
    return Path(state_dir) / f"{job_name}.throttle.json"


def _read_last_success(path: Path) -> Optional[float]:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return float(data.get("last_success", 0))
    except (json.JSONDecodeError, ValueError):
        return None


def _write_last_success(path: Path, ts: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_success": ts}))


def check_throttle(config: ThrottleConfig, job_name: str) -> tuple[bool, str]:
    """Return (allowed, reason). allowed=False means skip this run."""
    if not config.enabled:
        return True, "throttle disabled"
    path = _state_path(job_name, config.state_dir)
    last = _read_last_success(path)
    if last is None:
        return True, "no previous run recorded"
    elapsed = time.time() - last
    if elapsed < config.min_interval_seconds:
        remaining = config.min_interval_seconds - elapsed
        return False, f"throttled: {remaining:.1f}s remaining before next allowed run"
    return True, f"interval satisfied ({elapsed:.1f}s >= {config.min_interval_seconds}s)"


def record_throttle_success(config: ThrottleConfig, job_name: str) -> None:
    """Record a successful run timestamp for throttle tracking."""
    if not config.enabled:
        return
    path = _state_path(job_name, config.state_dir)
    _write_last_success(path, time.time())


def reset_throttle(config: ThrottleConfig, job_name: str) -> None:
    """Clear throttle state for a job."""
    path = _state_path(job_name, config.state_dir)
    if path.exists():
        path.unlink()
