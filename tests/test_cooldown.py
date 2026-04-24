"""Tests for cronwrap.cooldown."""
import json
import time
import pytest
from pathlib import Path
from cronwrap.cooldown import (
    CooldownConfig,
    check_cooldown,
    record_failure,
    clear_cooldown,
    _state_path,
)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


def make_cfg(tmp_dir, enabled=True, period=60, job_id="testjob"):
    return CooldownConfig(enabled=enabled, period=period, job_id=job_id, state_dir=tmp_dir)


def test_disabled_always_allows(tmp_dir):
    cfg = make_cfg(tmp_dir, enabled=False)
    allowed, remaining = check_cooldown(cfg)
    assert allowed is True
    assert remaining is None


def test_first_run_allowed(tmp_dir):
    cfg = make_cfg(tmp_dir)
    allowed, remaining = check_cooldown(cfg)
    assert allowed is True
    assert remaining is None


def test_blocked_after_failure(tmp_dir):
    cfg = make_cfg(tmp_dir, period=120)
    record_failure(cfg)
    allowed, remaining = check_cooldown(cfg)
    assert allowed is False
    assert remaining is not None
    assert 0 < remaining <= 120


def test_allowed_after_period_expires(tmp_dir):
    cfg = make_cfg(tmp_dir, period=1)
    record_failure(cfg)
    time.sleep(1.1)
    allowed, remaining = check_cooldown(cfg)
    assert allowed is True
    assert remaining is None


def test_clear_removes_state(tmp_dir):
    cfg = make_cfg(tmp_dir)
    record_failure(cfg)
    assert _state_path(cfg).exists()
    clear_cooldown(cfg)
    assert not _state_path(cfg).exists()


def test_clear_missing_file_ok(tmp_dir):
    cfg = make_cfg(tmp_dir)
    clear_cooldown(cfg)  # should not raise


def test_from_dict_full(tmp_dir):
    cfg = CooldownConfig.from_dict({
        "enabled": True,
        "period": 90,
        "job_id": "myjob",
        "state_dir": tmp_dir,
    })
    assert cfg.enabled is True
    assert cfg.period == 90
    assert cfg.job_id == "myjob"


def test_from_dict_defaults():
    cfg = CooldownConfig.from_dict({})
    assert cfg.enabled is False
    assert cfg.period == 300
    assert cfg.job_id == "default"


def test_corrupted_state_allows_run(tmp_dir):
    cfg = make_cfg(tmp_dir)
    p = _state_path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not-valid-json")
    allowed, remaining = check_cooldown(cfg)
    assert allowed is True
