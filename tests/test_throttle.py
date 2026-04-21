"""Tests for cronwrap.throttle."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.throttle import (
    ThrottleConfig,
    check_throttle,
    record_throttle_success,
    reset_throttle,
    _state_path,
)


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


def make_config(tmp_dir, interval=60):
    return ThrottleConfig(min_interval_seconds=interval, state_dir=tmp_dir)


def test_throttle_disabled_always_allows(tmp_dir):
    cfg = ThrottleConfig(min_interval_seconds=0, state_dir=tmp_dir)
    allowed, reason = check_throttle(cfg, "myjob")
    assert allowed is True
    assert "disabled" in reason


def test_first_run_allowed(tmp_dir):
    cfg = make_config(tmp_dir)
    allowed, reason = check_throttle(cfg, "myjob")
    assert allowed is True
    assert "no previous" in reason


def test_run_too_soon_blocked(tmp_dir):
    cfg = make_config(tmp_dir, interval=3600)
    record_throttle_success(cfg, "myjob")
    allowed, reason = check_throttle(cfg, "myjob")
    assert allowed is False
    assert "throttled" in reason


def test_run_after_interval_allowed(tmp_dir):
    cfg = make_config(tmp_dir, interval=1)
    path = _state_path("myjob", tmp_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_success": time.time() - 10}))
    allowed, reason = check_throttle(cfg, "myjob")
    assert allowed is True
    assert "satisfied" in reason


def test_record_writes_file(tmp_dir):
    cfg = make_config(tmp_dir)
    record_throttle_success(cfg, "myjob")
    path = _state_path("myjob", tmp_dir)
    assert path.exists()
    data = json.loads(path.read_text())
    assert "last_success" in data
    assert data["last_success"] <= time.time()


def test_reset_removes_file(tmp_dir):
    cfg = make_config(tmp_dir)
    record_throttle_success(cfg, "myjob")
    reset_throttle(cfg, "myjob")
    path = _state_path("myjob", tmp_dir)
    assert not path.exists()


def test_reset_missing_file_ok(tmp_dir):
    cfg = make_config(tmp_dir)
    reset_throttle(cfg, "myjob")  # should not raise


def test_record_disabled_does_nothing(tmp_dir):
    cfg = ThrottleConfig(min_interval_seconds=0, state_dir=tmp_dir)
    record_throttle_success(cfg, "myjob")
    path = _state_path("myjob", tmp_dir)
    assert not path.exists()


def test_from_dict_full():
    cfg = ThrottleConfig.from_dict({"min_interval_seconds": 120, "state_dir": "/tmp/x"})
    assert cfg.min_interval_seconds == 120
    assert cfg.state_dir == "/tmp/x"
    assert cfg.enabled is True


def test_from_dict_defaults():
    cfg = ThrottleConfig.from_dict({})
    assert cfg.min_interval_seconds == 0
    assert cfg.enabled is False
