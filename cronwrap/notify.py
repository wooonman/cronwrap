"""Notification hooks: slack and webhook support."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class NotifyConfig:
    slack_webhook_url: Optional[str] = None
    generic_webhook_url: Optional[str] = None
    on_failure: bool = True
    on_success: bool = False
    extra_headers: dict = field(default_factory=dict)


def _post_json(url: str, payload: dict, extra_headers: dict = {}) -> bool:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in extra_headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except urllib.error.URLError as e:
        logger.warning("Webhook request failed: %s", e)
        return False


def send_slack(url: str, message: str) -> bool:
    return _post_json(url, {"text": message})


def send_webhook(url: str, payload: dict, extra_headers: dict = {}) -> bool:
    return _post_json(url, payload, extra_headers)


def maybe_notify(config: NotifyConfig, success: bool, command: str, output: str, exit_code: int) -> None:
    if success and not config.on_success:
        return
    if not success and not config.on_failure:
        return

    status_str = "succeeded" if success else "failed"
    message = f"[cronwrap] Command `{command}` {status_str} (exit {exit_code}).\n{output[:500]}"

    if config.slack_webhook_url:
        ok = send_slack(config.slack_webhook_url, message)
        logger.debug("Slack notify sent: %s", ok)

    if config.generic_webhook_url:
        payload = {
            "command": command,
            "success": success,
            "exit_code": exit_code,
            "output": output[:500],
        }
        ok = send_webhook(config.generic_webhook_url, payload, config.extra_headers)
        logger.debug("Webhook notify sent: %s", ok)
