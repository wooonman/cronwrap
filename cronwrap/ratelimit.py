"""Rate limiting: prevent a job from running more than N times in a window."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class RateLimitConfig:
    max_runs: int
    window_seconds: int


def _rate_file(job_name: str, base_dir: str = "/tmp/cronwrap/ratelimit") -> Path:
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    safe = job_name.replace("/", "_").replace(" ", "_")
    return Path(base_dir) / f"{safe}.json"


def _read_timestamps(path: Path) -> List[float]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _write_timestamps(path: Path, timestamps: List[float]) -> None:
    path.write_text(json.dumps(timestamps))


def check_rate_limit(
    job_name: str,
    config: RateLimitConfig,
    base_dir: str = "/tmp/cronwrap/ratelimit",
) -> bool:
    """Return True if the job is allowed to run, False if rate-limited."""
    path = _rate_file(job_name, base_dir)
    now = time.time()
    cutoff = now - config.window_seconds
    timestamps = [t for t in _read_timestamps(path) if t >= cutoff]
    if len(timestamps) >= config.max_runs:
        return False
    timestamps.append(now)
    _write_timestamps(path, timestamps)
    return True


def reset_rate_limit(
    job_name: str,
    base_dir: str = "/tmp/cronwrap/ratelimit",
) -> None:
    """Clear recorded timestamps for a job."""
    path = _rate_file(job_name, base_dir)
    if path.exists():
        path.unlink()


def runs_in_window(
    job_name: str,
    window_seconds: int,
    base_dir: str = "/tmp/cronwrap/ratelimit",
) -> int:
    """Return how many runs have been recorded within the window."""
    path = _rate_file(job_name, base_dir)
    now = time.time()
    cutoff = now - window_seconds
    return sum(1 for t in _read_timestamps(path) if t >= cutoff)
