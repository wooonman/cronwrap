"""Middleware that enforces retry policy around command execution."""
from __future__ import annotations

from cronwrap.middleware import MiddlewareChain
from cronwrap.retry import RetryPolicy, RetryState


class RetryMiddleware:
    """Stores retry policy and result on the run context."""

    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy

    def pre(self, context) -> None:
        context.retry_policy = self.policy
        context.retry_state = None

    def post(self, context, result) -> None:
        state: RetryState | None = getattr(result, "retry_state", None)
        context.retry_state = state
        if state is not None:
            context.extra = getattr(context, "extra", {})
            context.extra["retry_attempts"] = state.total_attempts
            context.extra["retry_gave_up"] = state.gave_up


def attach_retry_middleware(
    chain: MiddlewareChain, policy: RetryPolicy
) -> RetryMiddleware:
    mw = RetryMiddleware(policy)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
