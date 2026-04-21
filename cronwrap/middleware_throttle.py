"""Middleware that enforces throttle logic before running a job."""
from __future__ import annotations

from cronwrap.middleware import MiddlewareChain
from cronwrap.throttle import ThrottleConfig, check_throttle, record_throttle_success


class ThrottleMiddleware:
    def __init__(self, config: ThrottleConfig, job_name: str) -> None:
        self.config = config
        self.job_name = job_name

    def pre(self, context) -> None:
        allowed, reason = check_throttle(self.config, self.job_name)
        context.throttle_allowed = allowed
        context.throttle_reason = reason
        if not allowed:
            # Signal to the runner that this run should be skipped
            context.skip = True
            context.skip_reason = reason

    def post(self, context, result) -> None:
        if result is not None and result.exit_code == 0:
            record_throttle_success(self.config, self.job_name)


def attach_throttle_middleware(
    chain: MiddlewareChain,
    config: ThrottleConfig,
    job_name: str,
) -> None:
    mw = ThrottleMiddleware(config, job_name)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
