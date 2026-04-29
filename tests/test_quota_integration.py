"""Integration test: quota middleware wired into a MiddlewareChain."""
from __future__ import annotations

import pytest

from cronwrap.quota import QuotaConfig, record_run
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_quota import attach_quota_middleware


class FakeContext:
    def __init__(self):
        self.quota_used_seconds = None
        self.quota_duration = None


class FakeResult:
    def __init__(self, exit_code=0, duration=2.0):
        self.exit_code = exit_code
        self.duration = duration


def simulate(cfg: QuotaConfig, result_duration: float = 2.0):
    chain = MiddlewareChain()
    attach_quota_middleware(chain, cfg)
    ctx = FakeContext()
    chain.run_pre(ctx)
    result = FakeResult(duration=result_duration)
    chain.run_post(ctx, result)
    return ctx


@pytest.fixture
def tmp_cfg(tmp_path):
    return QuotaConfig(
        job_id="integration-job",
        max_seconds=8.0,
        window_seconds=3600.0,
        state_dir=str(tmp_path),
    )


def test_single_run_within_quota(tmp_cfg):
    ctx = simulate(tmp_cfg)
    assert ctx.quota_used_seconds == 0.0
    assert ctx.quota_duration >= 0.0


def test_cumulative_runs_blocked(tmp_cfg):
    record_run(tmp_cfg, 5.0)
    record_run(tmp_cfg, 4.0)  # total = 9 > 8
    chain = MiddlewareChain()
    attach_quota_middleware(chain, tmp_cfg)
    ctx = FakeContext()
    with pytest.raises(RuntimeError, match="quota"):
        chain.run_pre(ctx)


def test_disabled_quota_full_pipeline(tmp_path):
    cfg = QuotaConfig(job_id="disabled", max_seconds=0.0, state_dir=str(tmp_path))
    ctx = simulate(cfg)
    # disabled: nothing written to context
    assert ctx.quota_used_seconds is None
    assert ctx.quota_duration is None
