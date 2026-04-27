"""Time budget enforcement: fail a job if cumulative runtime exceeds a rolling window budget."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BudgetConfig:
    enabled: bool = False
    max_seconds: float = 0.0          # total allowed seconds in the window
    window_seconds: float = 3600.0    # rolling window length in seconds
    job_name: str = "default"
    state_dir: str = "/tmp/cronwrap/budget"

    @classmethod
    def from_dict(cls, d: dict) -> "BudgetConfig":
        return cls(
            enabled=bool(d.get("enabled", False)),
            max_seconds=float(d.get("max_seconds", 0.0)),
            window_seconds=float(d.get("window_seconds", 3600.0)),
            job_name=str(d.get("job_name", "default")),
            state_dir=str(d.get("state_dir", "/tmp/cronwrap/budget")),
        )

    def is_enabled(self) -> bool:
        return self.enabled and self.max_seconds > 0


def _state_path(cfg: BudgetConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.job_name}.json"


def _read_runs(cfg: BudgetConfig) -> List[float]:
    p = _state_path(cfg)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return [float(x) for x in data.get("runs", [])]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def _write_runs(cfg: BudgetConfig, runs: List[float]) -> None:
    p = _state_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"runs": runs}))


def _prune(runs: List[float], window: float, now: float) -> List[float]:
    cutoff = now - window
    return [r for r in runs if r >= cutoff]


def check_budget(cfg: BudgetConfig, duration: float) -> bool:
    """Record *duration* and return True if still within budget, False if exceeded."""
    if not cfg.is_enabled():
        return True
    now = time.time()
    runs = _prune(_read_runs(cfg), cfg.window_seconds, now)
    runs.append(duration)
    _write_runs(cfg, runs)
    total = sum(runs)
    return total <= cfg.max_seconds


def remaining_budget(cfg: BudgetConfig) -> Optional[float]:
    """Return remaining seconds in the current window, or None if disabled."""
    if not cfg.is_enabled():
        return None
    now = time.time()
    runs = _prune(_read_runs(cfg), cfg.window_seconds, now)
    used = sum(runs)
    return max(0.0, cfg.max_seconds - used)


def reset_budget(cfg: BudgetConfig) -> None:
    """Clear all recorded runs for this job."""
    p = _state_path(cfg)
    if p.exists():
        p.unlink()
