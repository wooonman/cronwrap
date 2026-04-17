"""Environment variable injection for cron jobs."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvConfig:
    vars: Dict[str, str] = field(default_factory=dict)
    inherit: bool = True
    mask: List[str] = field(default_factory=list)  # keys to redact in logs


def build_env(config: EnvConfig) -> Dict[str, str]:
    """Build the environment dict to pass to subprocess."""
    base = dict(os.environ) if config.inherit else {}
    base.update(config.vars)
    return base


def redact_env(env: Dict[str, str], mask: List[str]) -> Dict[str, str]:
    """Return a copy with masked values replaced by '***'."""
    redacted = dict(env)
    for key in mask:
        if key in redacted:
            redacted[key] = "***"
    return redacted


def env_from_dict(data: dict) -> EnvConfig:
    """Build EnvConfig from a plain dict (e.g. loaded from config file)."""
    return EnvConfig(
        vars=data.get("vars", {}),
        inherit=data.get("inherit", True),
        mask=data.get("mask", []),
    )


def describe_env(config: EnvConfig) -> str:
    """Human-readable summary of env config."""
    lines = []
    if config.inherit:
        lines.append("inherits parent environment")
    else:
        lines.append("isolated environment (no inherit)")
    if config.vars:
        lines.append(f"injects {len(config.vars)} variable(s): {', '.join(config.vars.keys())}")
    if config.mask:
        lines.append(f"masks {len(config.mask)} variable(s) in logs")
    return "; ".join(lines)
