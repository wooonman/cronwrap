"""Middleware that enforces circuit-breaker logic around job execution."""
from __future__ import annotations

from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    is_open,
    record_outcome,
)
from cronwrap.middleware import MiddlewareChain


class CircuitBreakerMiddleware:
    """Pre-hook blocks execution when circuit is open; post-hook records outcome."""

    def __init__(self, cfg: CircuitBreakerConfig) -> None:
        self.cfg = cfg

    def pre(self, context) -> None:
        """Abort run if circuit is open by setting a skip flag on context."""
        if is_open(self.cfg):
            context.circuit_open = True
        else:
            context.circuit_open = False

    def post(self, context, result) -> None:
        """Record success or failure to update circuit state."""
        success = result.exit_code == 0
        state = record_outcome(self.cfg, success)
        context.circuit_state = state.as_dict()


def attach_circuit_breaker_middleware(
    chain: MiddlewareChain,
    cfg: CircuitBreakerConfig,
) -> CircuitBreakerMiddleware:
    mw = CircuitBreakerMiddleware(cfg)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
