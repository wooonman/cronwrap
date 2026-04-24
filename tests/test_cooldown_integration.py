"""Integration test: cooldown wired through MiddlewareChain."""
import pytest
from cronwrap.cooldown import CooldownConfig, _state_path
from cronwrap.middleware_cooldown import attach_cooldown_middleware
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


def run_pipeline(chain, ctx, result):
    chain.run_pre(ctx)
    chain.run_post(ctx, result)


def test_successful_run_clears_any_prior_failure(tmp_dir):
    cfg = CooldownConfig(enabled=True, period=300, job_id="integ", state_dir=tmp_dir)
    # Simulate a prior failure state
    from cronwrap.cooldown import record_failure
    record_failure(cfg)
    assert _state_path(cfg).exists()

    chain = MiddlewareChain()
    attach_cooldown_middleware(chain, cfg)
    ctx = FakeContext()
    result = FakeResult(exit_code=0)
    run_pipeline(chain, ctx, result)
    assert not _state_path(cfg).exists()


def test_failed_run_writes_state(tmp_dir):
    cfg = CooldownConfig(enabled=True, period=300, job_id="integ2", state_dir=tmp_dir)
    chain = MiddlewareChain()
    attach_cooldown_middleware(chain, cfg)
    ctx = FakeContext()
    result = FakeResult(exit_code=2)
    run_pipeline(chain, ctx, result)
    assert _state_path(cfg).exists()


def test_second_run_blocked_after_failure(tmp_dir):
    cfg = CooldownConfig(enabled=True, period=300, job_id="integ3", state_dir=tmp_dir)
    chain = MiddlewareChain()
    attach_cooldown_middleware(chain, cfg)

    # First run fails
    ctx = FakeContext()
    chain.run_pre(ctx)
    chain.run_post(ctx, FakeResult(exit_code=1))

    # Second run should be blocked
    chain2 = MiddlewareChain()
    attach_cooldown_middleware(chain2, cfg)
    ctx2 = FakeContext()
    with pytest.raises(RuntimeError, match="cooling down"):
        chain2.run_pre(ctx2)


def test_disabled_never_blocks(tmp_dir):
    cfg = CooldownConfig(enabled=False, period=300, job_id="integ4", state_dir=tmp_dir)
    from cronwrap.cooldown import record_failure
    record_failure(cfg)
    chain = MiddlewareChain()
    attach_cooldown_middleware(chain, cfg)
    ctx = FakeContext()
    chain.run_pre(ctx)  # should not raise
