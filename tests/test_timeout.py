"""Tests for cronwrap.timeout."""
import time
import pytest
from cronwrap.timeout import (
    TimeoutConfig,
    TimeoutExpired,
    from_dict,
    timeout_guard,
    describe_timeout,
)


def test_timeout_config_defaults():
    cfg = TimeoutConfig()
    assert cfg.seconds is None
    assert cfg.kill_on_expire is True
    assert not cfg.enabled


def test_timeout_config_enabled():
    cfg = TimeoutConfig(seconds=10)
    assert cfg.enabled


def test_timeout_config_zero_not_enabled():
    cfg = TimeoutConfig(seconds=0)
    assert not cfg.enabled


def test_from_dict_full():
    cfg = from_dict({"seconds": 30, "kill_on_expire": False, "message": "too slow"})
    assert cfg.seconds == 30
    assert cfg.kill_on_expire is False
    assert cfg.message == "too slow"


def test_from_dict_defaults():
    cfg = from_dict({})
    assert cfg.seconds is None
    assert cfg.kill_on_expire is True


def test_timeout_guard_no_timeout():
    cfg = TimeoutConfig()
    with timeout_guard(cfg):
        time.sleep(0.01)


def test_timeout_guard_completes_within_limit():
    cfg = TimeoutConfig(seconds=5)
    with timeout_guard(cfg):
        time.sleep(0.01)


def test_timeout_guard_raises_on_expire():
    cfg = TimeoutConfig(seconds=1, message="too slow")
    with pytest.raises(TimeoutExpired) as exc_info:
        with timeout_guard(cfg):
            time.sleep(2)
    assert exc_info.value.seconds == 1
    assert "too slow" in str(exc_info.value)


def test_describe_timeout_disabled():
    assert describe_timeout(TimeoutConfig()) == "no timeout"


def test_describe_timeout_enabled():
    result = describe_timeout(TimeoutConfig(seconds=15, kill_on_expire=False))
    assert "15s" in result
    assert "kill=False" in result
