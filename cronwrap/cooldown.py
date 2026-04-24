"""Cooldown: enforce a minimum wait period after a failure before allowing re-runs."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CooldownConfig:
    enabled: bool = False
    # seconds to wait after a failure before allowing the next run
    period: int = 300
    job_id: str = "default"
    state_dir: str = "/tmp/cronwrap/cooldown"

    @classmethod
    def from_dict(cls, data: dict) -> "CooldownConfig":
        return cls(
            enabled=data.get("enabled", False),
            period=int(data.get("period", 300)),
            job_id=data.get("job_id", "default"),
            state_dir=data.get("state_dir", "/tmp/cronwrap/cooldown"),
        )


def _state_path(cfg: CooldownConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.job_id}.cooldown.json"


def _read_failure_time(cfg: CooldownConfig) -> Optional[float]:
    p = _state_path(cfg)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
        return float(data.get("failed_at", 0))
    except (json.JSONDecodeError, ValueError):
        return None


def record_failure(cfg: CooldownConfig) -> None:
    """Record that the job failed right now."""
    p = _state_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"failed_at": time.time()}))


def clear_cooldown(cfg: CooldownConfig) -> None:
    """Clear cooldown state (e.g. after a successful run)."""
    p = _state_path(cfg)
    if p.exists():
        p.unlink()


def check_cooldown(cfg: CooldownConfig) -> tuple[bool, Optional[float]]:
    """Return (allowed, seconds_remaining). allowed=False means still cooling down."""
    if not cfg.enabled:
        return True, None
    failed_at = _read_failure_time(cfg)
    if failed_at is None:
        return True, None
    elapsed = time.time() - failed_at
    remaining = cfg.period - elapsed
    if remaining > 0:
        return False, remaining
    return True, None
