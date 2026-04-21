"""Tests for cronwrap.middleware_throttle."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.throttle import ThrottleConfig, _state_path
from cronwrap.middleware_throttle import ThrottleMiddleware, attach_throttle_middleware
from cronwrap.middleware import MiddlewareChain


class FakeContext:
    def __init__(self):
        self.skip = False
        self.skip_reason = ""
        self.throttle_allowed = None
        self.throttle_reason = ""


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


def make_config(tmp_dir, interval=3600):
    return ThrottleConfig(min_interval_seconds=interval, state_dir=tmp_dir)


def test_pre_allows_first_run(tmp_dir):
    cfg = make_config(tmp_dir)
    mw = ThrottleMiddleware(cfg, "job1")
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.throttle_allowed is True
    assert ctx.skip is False


def test_pre_blocks_too_soon(tmp_dir):
    cfg = make_config(tmp_dir)
    path = _state_path("job1", tmp_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_success": time.time()}))
    mw = ThrottleMiddleware(cfg, "job1")
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.throttle_allowed is False
    assert ctx.skip is True
    assert "throttled" in ctx.skip_reason


def test_post_records_on_success(tmp_dir):
    cfg = make_config(tmp_dir)
    mw = ThrottleMiddleware(cfg, "job1")
    ctx = FakeContext()
    result = FakeResult(exit_code=0)
    mw.post(ctx, result)
    path = _state_path("job1", tmp_dir)
    assert path.exists()


def test_post_skips_record_on_failure(tmp_dir):
    cfg = make_config(tmp_dir)
    mw = ThrottleMiddleware(cfg, "job1")
    ctx = FakeContext()
    result = FakeResult(exit_code=1)
    mw.post(ctx, result)
    path = _state_path("job1", tmp_dir)
    assert not path.exists()


def test_post_none_result_safe(tmp_dir):
    cfg = make_config(tmp_dir)
    mw = ThrottleMiddleware(cfg, "job1")
    ctx = FakeContext()
    mw.post(ctx, None)  # should not raise


def test_attach_adds_hooks(tmp_dir):
    cfg = make_config(tmp_dir)
    chain = MiddlewareChain()
    attach_throttle_middleware(chain, cfg, "job1")
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
