"""Tests for cronwrap.middleware_quota"""
from __future__ import annotations

import pytest

from cronwrap.quota import QuotaConfig, record_run, reset_quota
from cronwrap.middleware_quota import QuotaMiddleware, attach_quota_middleware
from cronwrap.middleware import MiddlewareChain


class FakeContext:
    def __init__(self):
        self.quota_used_seconds = None
        self.quota_duration = None


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code


@pytest.fixture
def tmp_cfg(tmp_path):
    return QuotaConfig(
        job_id="mw-job",
        max_seconds=10.0,
        window_seconds=3600.0,
        state_dir=str(tmp_path),
    )


def test_pre_sets_quota_used(tmp_cfg):
    mw = QuotaMiddleware(tmp_cfg)
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.quota_used_seconds == 0.0


def test_post_records_duration(tmp_cfg):
    mw = QuotaMiddleware(tmp_cfg)
    ctx = FakeContext()
    mw.pre(ctx)
    mw.post(ctx, FakeResult())
    assert ctx.quota_duration is not None
    assert ctx.quota_duration >= 0.0


def test_pre_raises_when_quota_exceeded(tmp_cfg):
    record_run(tmp_cfg, 10.5)
    mw = QuotaMiddleware(tmp_cfg)
    ctx = FakeContext()
    with pytest.raises(RuntimeError, match="quota"):
        mw.pre(ctx)


def test_disabled_quota_never_raises(tmp_path):
    cfg = QuotaConfig(job_id="x", max_seconds=0.0, state_dir=str(tmp_path))
    mw = QuotaMiddleware(cfg)
    ctx = FakeContext()
    mw.pre(ctx)   # should not raise
    mw.post(ctx, FakeResult())
    assert ctx.quota_used_seconds is None
    assert ctx.quota_duration is None


def test_attach_quota_middleware(tmp_cfg):
    chain = MiddlewareChain()
    attach_quota_middleware(chain, tmp_cfg)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
