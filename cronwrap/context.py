"""Runtime context passed through a cronwrap execution."""

import os
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RunContext:
    job_name: str
    command: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hostname: str = field(default_factory=socket.gethostname)
    pid: int = field(default_factory=os.getpid)
    run_id: str = ""
    lock_dir: str = "/tmp"
    log_file: Optional[str] = None
    dry_run: bool = False

    def __post_init__(self):
        if not self.run_id:
            ts = int(self.started_at.timestamp())
            self.run_id = f"{self.job_name}-{self.pid}-{ts}"

    def as_dict(self) -> dict:
        return {
            "job_name": self.job_name,
            "command": self.command,
            "started_at": self.started_at.isoformat(),
            "hostname": self.hostname,
            "pid": self.pid,
            "run_id": self.run_id,
        }


def make_context(job_name: str, command: str, **kwargs) -> RunContext:
    """Factory for creating a RunContext with optional overrides."""
    return RunContext(job_name=job_name, command=command, **kwargs)
