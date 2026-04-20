"""Middleware that suppresses logging/alerting based on FilterConfig."""

from __future__ import annotations

from cronwrap.filter import FilterConfig, should_suppress
from cronwrap.middleware import MiddlewareChain


class FilterMiddleware:
    def __init__(self, config: FilterConfig) -> None:
        self.config = config

    def pre(self, context: object) -> None:
        # Nothing to do before the run
        pass

    def post(self, context: object, result: object) -> None:
        """Attach a suppressed flag to the result if it matches filter rules."""
        suppressed = should_suppress(self.config, result)  # type: ignore[arg-type]
        # Store suppression decision on the result object so downstream
        # components (alerts, log_store) can check it.
        result.suppressed = suppressed  # type: ignore[union-attr]


def attach_filter_middleware(
    chain: MiddlewareChain, config: FilterConfig
) -> FilterMiddleware:
    mw = FilterMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
