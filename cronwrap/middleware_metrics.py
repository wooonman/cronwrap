"""Middleware hooks that record metrics automatically."""
from __future__ import annotations

import time
from typing import Any, Dict

from cronwrap.metrics import RunMetric, record_metric
from cronwrap.context import RunContext


class MetricsMiddleware:
    """Pre/post hooks compatible with MiddlewareChain that record RunMetrics."""

    def __init__(self, base_dir: str = "/tmp/cronwrap/metrics"):
        self.base_dir = base_dir
        self._start_times: Dict[str, float] = {}

    def pre(self, context: RunContext) -> None:
        self._start_times[context.run_id] = time.monotonic()

    def post(self, context: RunContext, result: Any) -> None:
        started = self._start_times.pop(context.run_id, time.monotonic())
        duration = round(time.monotonic() - started, 4)
        metric = RunMetric(
            job_name=context.job_name,
            started_at=context.started_at,
            duration_seconds=duration,
            exit_code=result.exit_code,
            retries=result.attempts - 1 if hasattr(result, "attempts") else 0,
            timed_out=getattr(result, "timed_out", False),
            tags={"run_id": context.run_id, "host": context.hostname},
        )
        record_metric(metric, base_dir=self.base_dir)


def attach_metrics_middleware(chain: Any, base_dir: str = "/tmp/cronwrap/metrics") -> MetricsMiddleware:
    """Attach MetricsMiddleware pre/post hooks to an existing MiddlewareChain."""
    mw = MetricsMiddleware(base_dir=base_dir)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
