"""Webhook-based run log shipping — POST run results to a remote endpoint."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WebhookLogConfig:
    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    include_output: bool = True
    timeout_seconds: int = 10
    on_success: bool = True
    on_failure: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookLogConfig":
        return cls(
            url=data.get("url", ""),
            headers=data.get("headers", {}),
            include_output=data.get("include_output", True),
            timeout_seconds=int(data.get("timeout_seconds", 10)),
            on_success=data.get("on_success", True),
            on_failure=data.get("on_failure", True),
        )

    def enabled(self) -> bool:
        return bool(self.url)


def _build_payload(
    config: WebhookLogConfig,
    result: Any,
    context: Optional[Any] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "exit_code": result.exit_code,
        "success": result.exit_code == 0,
        "duration": getattr(result, "duration", None),
        "command": getattr(result, "command", None),
    }
    if config.include_output:
        payload["stdout"] = getattr(result, "stdout", "")
        payload["stderr"] = getattr(result, "stderr", "")
    if context is not None:
        payload["run_id"] = getattr(context, "run_id", None)
        payload["job_name"] = getattr(context, "job_name", None)
    return payload


def ship_log(
    config: WebhookLogConfig,
    result: Any,
    context: Optional[Any] = None,
) -> bool:
    """POST the run result to the configured webhook URL. Returns True on success."""
    if not config.enabled():
        return False

    success = result.exit_code == 0
    if success and not config.on_success:
        return False
    if not success and not config.on_failure:
        return False

    payload = _build_payload(config, result, context)
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", **config.headers}

    req = urllib.request.Request(config.url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_seconds) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError):
        return False
