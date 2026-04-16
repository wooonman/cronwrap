"""Append-only JSONL log store for run results."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class LogEntry:
    timestamp: str
    command: str
    exit_code: int
    duration: float
    stdout: str
    stderr: str
    attempts: int

    def __post_init__(self) -> None:
        self.exit_code = int(self.exit_code)
        self.duration = float(self.duration)
        self.attempts = int(self.attempts)


def append_log(path: Path, entry: LogEntry) -> None:
    """Append a single log entry to the JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(entry)) + "\n")


def read_logs(path: Path) -> List[LogEntry]:
    """Read all log entries from a JSONL file."""
    if not path.exists():
        return []
    entries: List[LogEntry] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(LogEntry(**json.loads(line)))
    return entries


def tail_logs(path: Path, n: int = 10) -> List[LogEntry]:
    """Return the last *n* log entries."""
    entries = read_logs(path)
    return entries[-n:]
