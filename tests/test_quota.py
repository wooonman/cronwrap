"""Tests for cronwrap.quota"""
from __future__ import annotations

import time
import pytest

from cronwrap.quota import (
    QuotaConfig,
    check_quota,
    record_run,
    reset_quota,
    _state_path,
)


@pytest.fixture
def tmp_cfg(tmp_path):
    return QuotaConfig(
        job_id="test-job",
        max_seconds=10.0,
        window_seconds=3600.0,
        state_dir=str(tmp_path),
    )


def test_disabled_always_allows(tmp_path):
    cfg = QuotaConfig(job_id="x", max_seconds=0.0, state_dir=str(tmp_path))
    allowed, used = check_quota(cfg)
    assert allowed is True
    assert used == 0.0


def test_first_run_allowed(tmp_cfg):
    allowed, used = check_quota(tmp_cfg)
    assert allowed is True
    assert used == 0.0


def test_within_quota(tmp_cfg):
    record_run(tmp_cfg, 4.0)
    record_run(tmp_cfg, 3.0)
    allowed, used = check_quota(tmp_cfg)
    assert allowed is True
    assert abs(used - 7.0) < 0.01


def test_exceeds_quota(tmp_cfg):
    record_run(tmp_cfg, 6.0)
    record_run(tmp_cfg, 5.0)
    allowed, used = check_quota(tmp_cfg)
    assert allowed is False
    assert used >= 10.0


def test_exactly_at_limit_blocked(tmp_cfg):
    record_run(tmp_cfg, 10.0)
    allowed, _ = check_quota(tmp_cfg)
    assert allowed is False


def test_reset_clears_state(tmp_cfg):
    record_run(tmp_cfg, 9.0)
    reset_quota(tmp_cfg)
    allowed, used = check_quota(tmp_cfg)
    assert allowed is True
    assert used == 0.0


def test_expired_runs_pruned(tmp_path):
    cfg = QuotaConfig(
        job_id="prune-job",
        max_seconds=5.0,
        window_seconds=1.0,   # 1-second window
        state_dir=str(tmp_path),
    )
    record_run(cfg, 4.9)
    time.sleep(1.1)
    allowed, used = check_quota(cfg)
    assert allowed is True
    assert used == 0.0


def test_from_dict(tmp_path):
    cfg = QuotaConfig.from_dict(
        "myjob",
        {"max_seconds": 60, "window_seconds": 7200, "state_dir": str(tmp_path)},
    )
    assert cfg.max_seconds == 60.0
    assert cfg.window_seconds == 7200.0
    assert cfg.job_id == "myjob"


def test_record_disabled_does_nothing(tmp_path):
    cfg = QuotaConfig(job_id="noop", max_seconds=0.0, state_dir=str(tmp_path))
    record_run(cfg, 999.0)
    assert not _state_path(cfg).exists()
