"""Tests for cronwrap.middleware_cooldown."""
import pytest
from cronwrap.cooldown import CooldownConfig, record_failure, _state_path
from cronwrap.middleware_cooldown import CooldownMiddleware, attach_cooldown_middleware
from cronwrap.middleware import MiddlewareChain


class FakeContext:
    def __init__(self):
        self.__dict__ = {}


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


def make_cfg(tmp_dir, enabled=True, period=60):
    return CooldownConfig(enabled=enabled, period=period, job_id="mw-test", state_dir=tmp_dir)


def test_pre_sets_cfg_on_context(tmp_dir):
    cfg = make_cfg(tmp_dir)
    mw = CooldownMiddleware(cfg)
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.__dict__["cooldown_cfg"] is cfg


def test_pre_blocks_during_cooldown(tmp_dir):
    cfg = make_cfg(tmp_dir, period=300)
    record_failure(cfg)
    mw = CooldownMiddleware(cfg)
    ctx = FakeContext()
    with pytest.raises(RuntimeError, match="cooling down"):
        mw.pre(ctx)


def test_post_records_failure(tmp_dir):
    cfg = make_cfg(tmp_dir)
    mw = CooldownMiddleware(cfg)
    ctx = FakeContext()
    result = FakeResult(exit_code=1)
    mw.post(ctx, result)
    assert _state_path(cfg).exists()


def test_post_clears_on_success(tmp_dir):
    cfg = make_cfg(tmp_dir)
    record_failure(cfg)
    assert _state_path(cfg).exists()
    mw = CooldownMiddleware(cfg)
    ctx = FakeContext()
    result = FakeResult(exit_code=0)
    mw.post(ctx, result)
    assert not _state_path(cfg).exists()


def test_attach_adds_hooks(tmp_dir):
    cfg = make_cfg(tmp_dir)
    chain = MiddlewareChain()
    attach_cooldown_middleware(chain, cfg)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
