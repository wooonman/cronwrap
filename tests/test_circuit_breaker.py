"""Tests for cronwrap.circuit_breaker."""
import time
import pytest
from cronwrap.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitState,
    is_open,
    record_outcome,
    reset_circuit,
    _read_state,
)


@pytest.fixture
def tmp_cfg(tmp_path):
    return CircuitBreakerConfig(
        enabled=True,
        failure_threshold=3,
        recovery_timeout=60,
        job_name="test_job",
        state_dir=str(tmp_path),
    )


def test_circuit_starts_closed(tmp_cfg):
    assert is_open(tmp_cfg) is False


def test_disabled_always_closed(tmp_path):
    cfg = CircuitBreakerConfig(enabled=False, state_dir=str(tmp_path))
    for _ in range(10):
        record_outcome(cfg, success=False)
    assert is_open(cfg) is False


def test_opens_after_threshold(tmp_cfg):
    for _ in range(3):
        record_outcome(tmp_cfg, success=False)
    assert is_open(tmp_cfg) is True


def test_does_not_open_below_threshold(tmp_cfg):
    for _ in range(2):
        record_outcome(tmp_cfg, success=False)
    assert is_open(tmp_cfg) is False


def test_success_resets_failures(tmp_cfg):
    record_outcome(tmp_cfg, success=False)
    record_outcome(tmp_cfg, success=False)
    record_outcome(tmp_cfg, success=True)
    state = _read_state(tmp_cfg)
    assert state.status == "closed"
    assert state.consecutive_failures == 0


def test_half_open_after_recovery_timeout(tmp_cfg, monkeypatch):
    for _ in range(3):
        record_outcome(tmp_cfg, success=False)
    assert is_open(tmp_cfg) is True
    # Simulate time passing beyond recovery_timeout
    monkeypatch.setattr(time, "time", lambda: time.time() + 120)
    assert is_open(tmp_cfg) is False
    state = _read_state(tmp_cfg)
    assert state.status == "half-open"


def test_reset_clears_state(tmp_cfg):
    for _ in range(3):
        record_outcome(tmp_cfg, success=False)
    reset_circuit(tmp_cfg)
    assert is_open(tmp_cfg) is False
    state = _read_state(tmp_cfg)
    assert state.status == "closed"
    assert state.consecutive_failures == 0


def test_from_dict():
    cfg = CircuitBreakerConfig.from_dict({
        "enabled": True,
        "failure_threshold": 5,
        "recovery_timeout": 120,
        "job_name": "myjob",
    })
    assert cfg.enabled is True
    assert cfg.failure_threshold == 5
    assert cfg.recovery_timeout == 120
    assert cfg.job_name == "myjob"


def test_from_dict_defaults():
    cfg = CircuitBreakerConfig.from_dict({})
    assert cfg.enabled is False
    assert cfg.failure_threshold == 3
    assert cfg.recovery_timeout == 300
