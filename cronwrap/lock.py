"""Simple file-based locking to prevent overlapping cron runs."""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LockInfo:
    pid: int
    started_at: float
    job_name: str


def _lock_path(job_name: str, lock_dir: str = "/tmp") -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return Path(lock_dir) / f"cronwrap_{safe}.lock"


def acquire_lock(job_name: str, lock_dir: str = "/tmp") -> Optional[Path]:
    """Try to acquire a lock. Returns lock path on success, None if already locked."""
    path = _lock_path(job_name, lock_dir)
    if path.exists():
        try:
            data = path.read_text().strip().split(",")
            pid = int(data[0])
            # Check if process is still alive
            os.kill(pid, 0)
            return None  # Process alive, lock held
        except (ProcessLookupError, OSError):
            pass  # Stale lock, take it over
        except (ValueError, IndexError):
            pass  # Corrupt lock file, overwrite

    path.write_text(f"{os.getpid()},{time.time()},{job_name}")
    return path


def release_lock(lock_path: Path) -> None:
    """Release a lock by removing the lock file."""
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def read_lock(job_name: str, lock_dir: str = "/tmp") -> Optional[LockInfo]:
    """Read info from an existing lock file."""
    path = _lock_path(job_name, lock_dir)
    if not path.exists():
        return None
    try:
        parts = path.read_text().strip().split(",", 2)
        return LockInfo(pid=int(parts[0]), started_at=float(parts[1]), job_name=parts[2])
    except (ValueError, IndexError):
        return None
