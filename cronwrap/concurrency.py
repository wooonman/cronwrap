"""Concurrency limiter — caps how many instances of a job run simultaneously."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ConcurrencyConfig:
    max_instances: int = 1
    state_dir: str = "/tmp/cronwrap/concurrency"
    job_name: str = "default"
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "ConcurrencyConfig":
        return cls(
            max_instances=int(data.get("max_instances", 1)),
            state_dir=data.get("state_dir", "/tmp/cronwrap/concurrency"),
            job_name=data.get("job_name", "default"),
            enabled=bool(data.get("enabled", True)),
        )


def _state_path(cfg: ConcurrencyConfig) -> Path:
    return Path(cfg.state_dir) / f"{cfg.job_name}.json"


def _read_slots(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_slots(path: Path, slots: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(slots))


def _prune_dead_slots(slots: list[dict]) -> list[dict]:
    """Remove slots whose PID is no longer alive."""
    live = []
    for s in slots:
        pid = s.get("pid")
        if pid and _pid_alive(pid):
            live.append(s)
    return live


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def acquire_slot(cfg: ConcurrencyConfig, run_id: str) -> bool:
    """Try to acquire a concurrency slot. Returns True if acquired."""
    if not cfg.enabled or cfg.max_instances <= 0:
        return True

    path = _state_path(cfg)
    slots = _prune_dead_slots(_read_slots(path))

    if len(slots) >= cfg.max_instances:
        _write_slots(path, slots)
        return False

    slots.append({"run_id": run_id, "pid": os.getpid(), "started_at": time.time()})
    _write_slots(path, slots)
    return True


def release_slot(cfg: ConcurrencyConfig, run_id: str) -> None:
    """Release the slot held by this run_id."""
    path = _state_path(cfg)
    slots = _read_slots(path)
    slots = [s for s in slots if s.get("run_id") != run_id]
    _write_slots(path, slots)


def active_count(cfg: ConcurrencyConfig) -> int:
    """Return number of currently active (live) slots."""
    path = _state_path(cfg)
    return len(_prune_dead_slots(_read_slots(path)))
