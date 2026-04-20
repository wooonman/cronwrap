"""Output filtering: suppress runs from logs/alerts based on exit code or pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from cronwrap.runner import RunResult


@dataclass
class FilterConfig:
    suppress_on_success: bool = False
    suppress_exit_codes: List[int] = field(default_factory=list)
    suppress_output_patterns: List[str] = field(default_factory=list)
    suppress_empty_output: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "FilterConfig":
        return cls(
            suppress_on_success=data.get("suppress_on_success", False),
            suppress_exit_codes=data.get("suppress_exit_codes", []),
            suppress_output_patterns=data.get("suppress_output_patterns", []),
            suppress_empty_output=data.get("suppress_empty_output", False),
        )


def should_suppress(config: FilterConfig, result: RunResult) -> bool:
    """Return True if this result should be suppressed (not logged/alerted)."""
    if config.suppress_on_success and result.exit_code == 0:
        return True

    if result.exit_code in config.suppress_exit_codes:
        return True

    combined = (result.stdout or "") + (result.stderr or "")

    if config.suppress_empty_output and not combined.strip():
        return True

    for pattern in config.suppress_output_patterns:
        if re.search(pattern, combined):
            return True

    return False


def describe_filter(config: FilterConfig) -> str:
    """Return a human-readable description of the filter config."""
    parts: List[str] = []
    if config.suppress_on_success:
        parts.append("suppress on success")
    if config.suppress_exit_codes:
        codes = ", ".join(str(c) for c in config.suppress_exit_codes)
        parts.append(f"suppress exit codes [{codes}]")
    if config.suppress_empty_output:
        parts.append("suppress empty output")
    if config.suppress_output_patterns:
        parts.append(f"{len(config.suppress_output_patterns)} output pattern(s)")
    return "; ".join(parts) if parts else "no filters"
