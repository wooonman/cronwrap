"""Tests for cronwrap.debounce."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from cronwrap.debounce import (
    DebounceConfig,
    check_debounce,
    reset_debounce,
    _state_path,
)


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def make_config(tmp_dir: Path, cooldown: int = 60, job_id: str = "test-job") -> DebounceConfig:
    return DebounceConfig(
        job_id=job_id,
        cooldown_seconds=cooldown,
        state_dir=str(tmp_dir),
    )


def test_debounce_disabled_always_allows(tmp_dir):
    cfg = make_config(tmp_dir, cooldown=0)
    allowed, reason = check_debounce(cfg)
    assert allowed is True
    assert "disabled" in reason


def test_first_run_allowed(tmp_dir):
    cfg = make_config(tmp_dir)
    allowed, reason = check_debounce(cfg)
    assert allowed is True
    assert "allowed" in reason


def test_first_run_writes_state(tmp_dir):
    cfg = make_config(tmp_dir)
    check_debounce(cfg)
    path = _state_path(cfg)
    assert path.exists()
    data = json.loads(path.read_text())
    assert "last_run" in data


def test_run_within_cooldown_blocked(tmp_dir):
    cfg = make_config(tmp_dir, cooldown=3600)
    check_debounce(cfg)  # first run — allowed, writes state
    allowed, reason = check_debounce(cfg)  # second run — should be blocked
    assert allowed is False
    assert "debounced" in reason
    assert "remaining" in reason


def test_run_after_cooldown_allowed(tmp_dir, monkeypatch):
    cfg = make_config(tmp_dir, cooldown=1)
    # Write a timestamp far in the past
    path = _state_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_run": time.time() - 10}))

    allowed, reason = check_debounce(cfg)
    assert allowed is True


def test_reset_removes_state(tmp_dir):
    cfg = make_config(tmp_dir)
    check_debounce(cfg)
    assert _state_path(cfg).exists()
    result = reset_debounce(cfg)
    assert result is True
    assert not _state_path(cfg).exists()


def test_reset_missing_returns_false(tmp_dir):
    cfg = make_config(tmp_dir)
    result = reset_debounce(cfg)
    assert result is False


def test_from_dict_full(tmp_dir):
    cfg = DebounceConfig.from_dict({
        "job_id": "myjob",
        "cooldown_seconds": 120,
        "state_dir": str(tmp_dir),
    })
    assert cfg.job_id == "myjob"
    assert cfg.cooldown_seconds == 120
    assert cfg.state_dir == str(tmp_dir)


def test_from_dict_defaults():
    cfg = DebounceConfig.from_dict({})
    assert cfg.job_id == "default"
    assert cfg.cooldown_seconds == 0
    assert cfg.enabled() is False
