"""Middleware that enforces a rolling time budget per job."""

from __future__ import annotations

import time
from typing import Any

from cronwrap.budget import BudgetConfig, check_budget, remaining_budget
from cronwrap.middleware import MiddlewareChain


class BudgetMiddleware:
    """Pre/post hooks that track cumulative runtime and flag budget overruns."""

    def __init__(self, cfg: BudgetConfig) -> None:
        self.cfg = cfg
        self._start: float = 0.0

    def pre(self, context: Any) -> None:
        self._start = time.monotonic()
        if self.cfg.is_enabled():
            rem = remaining_budget(self.cfg)
            context.budget_remaining = rem
        else:
            context.budget_remaining = None

    def post(self, context: Any, result: Any) -> None:
        if not self.cfg.is_enabled():
            context.budget_exceeded = False
            return
        duration = time.monotonic() - self._start
        within = check_budget(self.cfg, duration)
        context.budget_exceeded = not within
        context.last_run_duration = duration
        if context.budget_exceeded:
            import logging
            logging.getLogger("cronwrap.budget").warning(
                "Budget exceeded for job '%s': %.2fs used this run; budget=%.2fs window=%.0fs",
                self.cfg.job_name,
                duration,
                self.cfg.max_seconds,
                self.cfg.window_seconds,
            )


def attach_budget_middleware(chain: MiddlewareChain, cfg: BudgetConfig) -> None:
    mw = BudgetMiddleware(cfg)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
