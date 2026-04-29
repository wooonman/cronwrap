"""Middleware that ships run results to a webhook after each run."""
from __future__ import annotations

from typing import Any

from cronwrap.middleware import MiddlewareChain
from cronwrap.webhook_log import WebhookLogConfig, ship_log


class WebhookLogMiddleware:
    """Pre is a no-op; post ships the run result to the configured webhook."""

    def __init__(self, config: WebhookLogConfig) -> None:
        self.config = config

    def pre(self, context: Any) -> None:
        pass

    def post(self, context: Any, result: Any) -> None:
        if not self.config.enabled():
            return
        shipped = ship_log(self.config, result, context)
        # Attach shipping status to context for observability / testing
        context.webhook_log_shipped = shipped


def attach_webhook_log_middleware(
    chain: MiddlewareChain,
    config: WebhookLogConfig,
) -> None:
    mw = WebhookLogMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
