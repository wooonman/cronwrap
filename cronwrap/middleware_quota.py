"""Middleware that enforces time-budget quotas per job."""
from __future__ import annotations

import time
from typing import Any

from cronwrap.middleware import MiddlewareChain
from cronwrap.quota import QuotaConfig, check_quota, record_run


class QuotaMiddleware:
    """Blocks execution when the rolling time quota is exhausted."""

    def __init__(self, cfg: QuotaConfig) -> None:
        self.cfg = cfg
        self._start: float = 0.0

    def pre(self, context: Any) -> None:
        if not self.cfg.is_enabled():
            return
        allowed, used = check_quota(self.cfg)
        context.quota_used_seconds = used
        if not allowed:
            raise RuntimeError(
                f"[quota] job '{self.cfg.job_id}' has consumed {used:.1f}s "
                f"of its {self.cfg.max_seconds:.1f}s quota "
                f"in the last {self.cfg.window_seconds:.0f}s window"
            )
        self._start = time.monotonic()

    def post(self, context: Any, result: Any) -> None:
        if not self.cfg.is_enabled():
            return
        duration = time.monotonic() - self._start
        record_run(self.cfg, duration)
        context.quota_duration = duration


def attach_quota_middleware(chain: MiddlewareChain, cfg: QuotaConfig) -> None:
    mw = QuotaMiddleware(cfg)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
