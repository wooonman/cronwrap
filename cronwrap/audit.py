"""Audit trail: record every cronwrap invocation with its outcome."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_DIR = os.path.expanduser("~/.cronwrap/audit")


@dataclass
class AuditEntry:
    run_id: str
    command: str
    started_at: str
    finished_at: str
    exit_code: int
    success: bool
    retries: int
    tags: List[str]
    host: str
    user: str
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


def _audit_path(audit_dir: str) -> Path:
    p = Path(audit_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p / "audit.jsonl"


def record_audit(entry: AuditEntry, audit_dir: str = DEFAULT_AUDIT_DIR) -> None:
    """Append a single audit entry to the audit log."""
    path = _audit_path(audit_dir)
    with path.open("a") as fh:
        fh.write(json.dumps(entry.as_dict()) + "\n")


def read_audit(audit_dir: str = DEFAULT_AUDIT_DIR) -> List[AuditEntry]:
    """Read all audit entries from the audit log."""
    path = _audit_path(audit_dir)
    if not path.exists():
        return []
    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                data = json.loads(line)
                entries.append(AuditEntry(**data))
    return entries


def make_audit_entry(
    run_id: str,
    command: str,
    exit_code: int,
    retries: int = 0,
    tags: Optional[List[str]] = None,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    note: Optional[str] = None,
) -> AuditEntry:
    """Convenience constructor that fills in host/user/timestamps automatically."""
    import socket
    import getpass

    now = datetime.now(timezone.utc).isoformat()
    return AuditEntry(
        run_id=run_id,
        command=command,
        started_at=started_at or now,
        finished_at=finished_at or now,
        exit_code=exit_code,
        success=exit_code == 0,
        retries=retries,
        tags=tags or [],
        host=socket.gethostname(),
        user=getpass.getuser(),
        note=note,
    )
