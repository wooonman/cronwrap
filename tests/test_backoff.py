"""Tests for cronwrap.backoff and cronwrap.middleware_backoff."""
import pytest
from unittest.mock import patch

from cronwrap.backoff import BackoffConfig
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_backoff import BackoffMiddleware, attach_backoff_middleware


# --- BackoffConfig tests ---

def test_default_strategy_constant():
    cfg = BackoffConfig()
    assert cfg.strategy == "constant"
    assert cfg.base_delay == 1.0


def test_enabled_with_positive_base():
    cfg = BackoffConfig(base_delay=2.0)
    assert cfg.enabled() is True


def test_disabled_when_zero_base():
    cfg = BackoffConfig(base_delay=0.0)
    assert cfg.enabled() is False


def test_constant_delay_same_for_all_attempts():
    cfg = BackoffConfig(strategy="constant", base_delay=3.0)
    assert cfg.delay_for(1) == 3.0
    assert cfg.delay_for(2) == 3.0
    assert cfg.delay_for(5) == 3.0


def test_linear_delay_scales_with_attempt():
    cfg = BackoffConfig(strategy="linear", base_delay=2.0)
    assert cfg.delay_for(1) == 2.0
    assert cfg.delay_for(3) == 6.0


def test_exponential_delay():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=2.0)
    assert cfg.delay_for(1) == 1.0
    assert cfg.delay_for(2) == 2.0
    assert cfg.delay_for(3) == 4.0


def test_max_delay_capped():
    cfg = BackoffConfig(strategy="exponential", base_delay=1.0, multiplier=10.0, max_delay=5.0)
    assert cfg.delay_for(10) == 5.0


def test_jitter_within_bounds():
    cfg = BackoffConfig(strategy="jitter", base_delay=4.0, multiplier=1.0, jitter_range=0.5, max_delay=100.0)
    for _ in range(50):
        delay = cfg.delay_for(1)
        assert 2.0 <= delay <= 6.0


def test_from_dict_full():
    cfg = BackoffConfig.from_dict({
        "strategy": "linear",
        "base_delay": 5.0,
        "max_delay": 30.0,
        "multiplier": 3.0,
        "jitter_range": 0.2,
    })
    assert cfg.strategy == "linear"
    assert cfg.base_delay == 5.0
    assert cfg.max_delay == 30.0


def test_from_dict_defaults():
    cfg = BackoffConfig.from_dict({})
    assert cfg.strategy == "constant"
    assert cfg.base_delay == 1.0


def test_describe_returns_string():
    cfg = BackoffConfig(strategy="exponential", base_delay=2.0)
    desc = cfg.describe()
    assert "exponential" in desc
    assert "2.0" in desc


def test_attempt_below_one_treated_as_one():
    cfg = BackoffConfig(strategy="constant", base_delay=5.0)
    assert cfg.delay_for(0) == cfg.delay_for(1)


# --- Middleware tests ---

class FakeContext:
    def __init__(self):
        self.backoff = None


class FakeResult:
    def __init__(self):
        self.exit_code = 0


def test_backoff_middleware_sets_config_on_context():
    cfg = BackoffConfig(strategy="linear", base_delay=2.0)
    mw = BackoffMiddleware(cfg)
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.backoff is cfg


def test_backoff_middleware_post_is_noop():
    cfg = BackoffConfig()
    mw = BackoffMiddleware(cfg)
    ctx = FakeContext()
    result = FakeResult()
    mw.post(ctx, result)  # should not raise


def test_attach_backoff_middleware_from_raw():
    chain = MiddlewareChain()
    cfg = attach_backoff_middleware(chain, raw={"strategy": "exponential", "base_delay": 3.0})
    assert cfg.strategy == "exponential"
    assert cfg.base_delay == 3.0


def test_attach_backoff_middleware_uses_provided_config():
    chain = MiddlewareChain()
    provided = BackoffConfig(strategy="jitter", base_delay=1.5)
    returned = attach_backoff_middleware(chain, config=provided)
    assert returned is provided
