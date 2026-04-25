"""Middleware that attaches a BackoffConfig to the run context."""
from __future__ import annotations

from cronwrap.backoff import BackoffConfig
from cronwrap.middleware import MiddlewareChain


class BackoffMiddleware:
    """Reads backoff config from context and stores it for use by retry logic."""

    def __init__(self, config: BackoffConfig) -> None:
        self.config = config

    def pre(self, context: object) -> None:
        """Attach the BackoffConfig to the run context before execution."""
        context.backoff = self.config  # type: ignore[attr-defined]

    def post(self, context: object, result: object) -> None:
        """No-op: backoff config is consumed during retry, nothing to clean up."""
        pass


def attach_backoff_middleware(
    chain: MiddlewareChain,
    config: BackoffConfig | None = None,
    raw: dict | None = None,
) -> BackoffConfig:
    """Convenience helper to build and attach BackoffMiddleware to a chain."""
    if config is None:
        config = BackoffConfig.from_dict(raw or {})
    mw = BackoffMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return config
