"""Load cronwrap configuration from a TOML or JSON file."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CronwrapConfig:
    retries: int = 0
    timeout: Optional[int] = None
    log_file: Optional[str] = None
    alert_email: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    generic_webhook_url: Optional[str] = None
    notify_on_success: bool = False
    notify_on_failure: bool = True
    extra_webhook_headers: dict = field(default_factory=dict)


def _load_toml(path: str) -> dict:
    try:
        import tomllib  # type: ignore
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            raise ImportError("Install 'tomli' for Python < 3.11 to read TOML configs.")
    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def load_config(path: str) -> CronwrapConfig:
    """Load a CronwrapConfig from a JSON or TOML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    if path.endswith(".toml"):
        data = _load_toml(path)
    elif path.endswith(".json"):
        data = _load_json(path)
    else:
        raise ValueError(f"Unsupported config format: {path}")

    return CronwrapConfig(
        retries=data.get("retries", 0),
        timeout=data.get("timeout"),
        log_file=data.get("log_file"),
        alert_email=data.get("alert_email"),
        slack_webhook_url=data.get("slack_webhook_url"),
        generic_webhook_url=data.get("generic_webhook_url"),
        notify_on_success=data.get("notify_on_success", False),
        notify_on_failure=data.get("notify_on_failure", True),
        extra_webhook_headers=data.get("extra_webhook_headers", {}),
    )
