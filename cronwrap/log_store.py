import json
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    command: str
    success: bool
    exit_code: int
    retries: int
    duration: float
    stdout: str
    stderr: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


def append_log(path: str, entry: LogEntry) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(asdict(entry)) + "\n")


def read_logs(path: str, last_n: Optional[int] = None) -> List[LogEntry]:
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(LogEntry(**json.loads(line)))
    if last_n is not None:
        entries = entries[-last_n:]
    return entries


def tail_logs(path: str, n: int = 10) -> List[LogEntry]:
    return read_logs(path, last_n=n)
