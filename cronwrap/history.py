"""Query and summarize past run history from the log store."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from cronwrap.log_store import read_logs, LogEntry


@dataclass
class RunSummary:
    total: int
    successes: int
    failures: int
    avg_duration: float
    last_status: Optional[str]

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.successes / self.total * 100


def get_history(log_path: Path, limit: int = 50) -> List[LogEntry]:
    """Return up to *limit* most recent log entries."""
    entries = read_logs(log_path)
    return entries[-limit:] if len(entries) > limit else entries


def summarize(entries: List[LogEntry]) -> RunSummary:
    """Compute aggregate stats over a list of log entries."""
    total = len(entries)
    successes = sum(1 for e in entries if e.exit_code == 0)
    failures = total - successes
    avg_duration = (
        sum(e.duration for e in entries) / total if total else 0.0
    )
    last_status = (
        ("success" if entries[-1].exit_code == 0 else "failure")
        if entries
        else None
    )
    return RunSummary(
        total=total,
        successes=successes,
        failures=failures,
        avg_duration=avg_duration,
        last_status=last_status,
    )


def filter_failures(entries: List[LogEntry]) -> List[LogEntry]:
    """Return only the entries where the command exited with a non-zero code."""
    return [e for e in entries if e.exit_code != 0]


def print_history(log_path: Path, limit: int = 20, failures_only: bool = False) -> None:
    """Pretty-print recent history to stdout.

    Args:
        log_path: Path to the log file.
        limit: Maximum number of recent entries to display.
        failures_only: When True, only failed runs are shown.
    """
    entries = get_history(log_path, limit)
    if not entries:
        print("No history found.")
        return
    if failures_only:
        entries = filter_failures(entries)
        if not entries:
            print("No failures found in recent history.")
            return
    summary = summarize(entries)
    print(f"Last {len(entries)} runs  |  "
          f"Success rate: {summary.success_rate:.1f}%  |  "
          f"Avg duration: {summary.avg_duration:.2f}s")
    print("-" * 60)
    for e in entries:
        status = "OK" if e.exit_code == 0 else "FAIL"
        print(f"[{e.timestamp}] {status:4s}  exit={e.exit_code}  "
              f"dur={e.duration:.2f}s  cmd={e.command}")
