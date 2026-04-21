"""Output redaction: mask sensitive patterns in command output before logging or alerting."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RedactorConfig:
    patterns: List[str] = field(default_factory=list)
    replacement: str = "***REDACTED***"
    case_sensitive: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "RedactorConfig":
        return cls(
            patterns=data.get("patterns", []),
            replacement=data.get("replacement", "***REDACTED***"),
            case_sensitive=data.get("case_sensitive", False),
        )

    def enabled(self) -> bool:
        return len(self.patterns) > 0


def _compile_patterns(config: RedactorConfig) -> List[re.Pattern]:
    flags = 0 if config.case_sensitive else re.IGNORECASE
    compiled = []
    for p in config.patterns:
        try:
            compiled.append(re.compile(p, flags))
        except re.error:
            # skip invalid patterns silently
            pass
    return compiled


def redact(text: str, config: RedactorConfig) -> str:
    """Return text with all matching patterns replaced by the configured replacement."""
    if not config.enabled() or not text:
        return text
    compiled = _compile_patterns(config)
    result = text
    for pattern in compiled:
        result = pattern.sub(config.replacement, result)
    return result


def redact_result(stdout: Optional[str], stderr: Optional[str], config: RedactorConfig):
    """Redact both stdout and stderr, returning (stdout, stderr) tuple."""
    return redact(stdout or "", config), redact(stderr or "", config)


def describe_redactor(config: RedactorConfig) -> str:
    if not config.enabled():
        return "redaction disabled"
    return (
        f"redacting {len(config.patterns)} pattern(s), "
        f"replacement={config.replacement!r}, "
        f"case_sensitive={config.case_sensitive}"
    )
