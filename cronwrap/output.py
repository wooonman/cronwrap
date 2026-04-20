"""Capture, truncate, and store command output (stdout/stderr)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB


@dataclass
class OutputConfig:
    max_bytes: int = DEFAULT_MAX_BYTES
    store_dir: Optional[str] = None
    include_stderr: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "OutputConfig":
        return cls(
            max_bytes=int(d.get("max_bytes", DEFAULT_MAX_BYTES)),
            store_dir=d.get("store_dir"),
            include_stderr=bool(d.get("include_stderr", True)),
        )


@dataclass
class CapturedOutput:
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    stored_path: Optional[str] = None

    def combined(self) -> str:
        parts = [p for p in (self.stdout, self.stderr) if p]
        return "\n".join(parts)


def truncate_output(text: str, max_bytes: int) -> tuple[str, bool]:
    """Return (possibly-truncated text, was_truncated)."""
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="replace")
    return truncated + "\n...[truncated]", True


def process_output(
    stdout: str,
    stderr: str,
    config: OutputConfig,
    run_id: Optional[str] = None,
) -> CapturedOutput:
    """Apply truncation and optional persistence to captured output."""
    combined = stdout
    if config.include_stderr and stderr:
        combined = stdout + ("\n" + stderr if stdout else stderr)

    text, was_truncated = truncate_output(combined, config.max_bytes)

    stored_path: Optional[str] = None
    if config.store_dir and run_id:
        stored_path = _store_output(text, config.store_dir, run_id)

    return CapturedOutput(
        stdout=stdout,
        stderr=stderr if config.include_stderr else "",
        truncated=was_truncated,
        stored_path=stored_path,
    )


def _store_output(text: str, store_dir: str, run_id: str) -> str:
    path = Path(store_dir)
    path.mkdir(parents=True, exist_ok=True)
    out_file = path / f"{run_id}.log"
    out_file.write_text(text, encoding="utf-8")
    return str(out_file)


def load_stored_output(store_dir: str, run_id: str) -> Optional[str]:
    path = Path(store_dir) / f"{run_id}.log"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
