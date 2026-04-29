"""Quota enforcement: cap total run-time (seconds) consumed within a rolling window."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class QuotaConfig:
    job_id: str
    max_seconds: float = 0.0          # 0 = disabled
    window_seconds: float = 86400.0   # default: 24-hour rolling window
    state_dir: str = "/tmp/cronwrap/quota"

    @classmethod
    def from_dict(cls, job_id: str, d: dict) -> "QuotaConfig":
        return cls(
            job_id=job_id,
            max_seconds=float(d.get("max_seconds", 0.0)),
            window_seconds=float(d.get("window_seconds", 86400.0)),
            state_dir=d.get("state_dir", "/tmp/cronwrap/quota"),
        )

    def is_enabled(self) -> bool:
        return self.max_seconds > 0


def _state_path(cfg: QuotaConfig) -> Path:
    p = Path(cfg.state_dir)
    p.mkdir(parents=True, exist_ok=True)
    safe = cfg.job_id.replace("/", "_").replace(" ", "_")
    return p / f"{safe}.json"


def _read_runs(cfg: QuotaConfig) -> List[dict]:
    path = _state_path(cfg)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _write_runs(cfg: QuotaConfig, runs: List[dict]) -> None:
    _state_path(cfg).write_text(json.dumps(runs))


def check_quota(cfg: QuotaConfig) -> tuple[bool, float]:
    """Return (allowed, used_seconds). Prunes expired entries before checking."""
    if not cfg.is_enabled():
        return True, 0.0
    now = time.time()
    cutoff = now - cfg.window_seconds
    runs = [r for r in _read_runs(cfg) if r["ts"] >= cutoff]
    used = sum(r["duration"] for r in runs)
    allowed = used < cfg.max_seconds
    _write_runs(cfg, runs)
    return allowed, used


def record_run(cfg: QuotaConfig, duration: float) -> None:
    """Append a completed run's duration to the rolling window state."""
    if not cfg.is_enabled():
        return
    now = time.time()
    cutoff = now - cfg.window_seconds
    runs = [r for r in _read_runs(cfg) if r["ts"] >= cutoff]
    runs.append({"ts": now, "duration": duration})
    _write_runs(cfg, runs)


def reset_quota(cfg: QuotaConfig) -> None:
    """Clear all recorded run history for this job."""
    path = _state_path(cfg)
    if path.exists():
        path.unlink()
