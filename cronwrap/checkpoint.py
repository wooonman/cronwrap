"""Checkpoint support — persist and restore run state across invocations."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Checkpoint:
    job_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    saved_at: float = field(default_factory=time.time)
    attempt: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "saved_at": self.saved_at,
            "attempt": self.attempt,
        }


def _checkpoint_path(job_id: str, directory: str) -> Path:
    safe = job_id.replace(os.sep, "_").replace(" ", "_")
    return Path(directory) / f"{safe}.checkpoint.json"


def save_checkpoint(checkpoint: Checkpoint, directory: str = "/tmp/cronwrap/checkpoints") -> Path:
    """Persist a checkpoint to disk. Returns the path written."""
    path = _checkpoint_path(checkpoint.job_id, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(checkpoint.as_dict(), fh, indent=2)
    return path


def load_checkpoint(job_id: str, directory: str = "/tmp/cronwrap/checkpoints") -> Optional[Checkpoint]:
    """Load a checkpoint from disk, or return None if it doesn't exist."""
    path = _checkpoint_path(job_id, directory)
    if not path.exists():
        return None
    with open(path) as fh:
        data = json.load(fh)
    return Checkpoint(
        job_id=data["job_id"],
        state=data.get("state", {}),
        saved_at=data.get("saved_at", 0.0),
        attempt=data.get("attempt", 0),
    )


def clear_checkpoint(job_id: str, directory: str = "/tmp/cronwrap/checkpoints") -> bool:
    """Remove a checkpoint file. Returns True if removed, False if it wasn't there."""
    path = _checkpoint_path(job_id, directory)
    if path.exists():
        path.unlink()
        return True
    return False


def checkpoint_age_seconds(checkpoint: Checkpoint) -> float:
    """Return how many seconds ago the checkpoint was saved."""
    return time.time() - checkpoint.saved_at
