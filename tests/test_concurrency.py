"""Tests for cronwrap.concurrency."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwrap.concurrency import (
    ConcurrencyConfig,
    acquire_slot,
    active_count,
    release_slot,
    _state_path,
)


@pytest.fixture()
def tmp_cfg(tmp_path):
    return ConcurrencyConfig(
        max_instances=2,
        state_dir=str(tmp_path),
        job_name="test_job",
        enabled=True,
    )


def test_from_dict_defaults():
    cfg = ConcurrencyConfig.from_dict({})
    assert cfg.max_instances == 1
    assert cfg.enabled is True
    assert cfg.job_name == "default"


def test_from_dict_custom():
    cfg = ConcurrencyConfig.from_dict({"max_instances": 3, "job_name": "nightly", "enabled": False})
    assert cfg.max_instances == 3
    assert cfg.job_name == "nightly"
    assert cfg.enabled is False


def test_first_acquire_succeeds(tmp_cfg):
    assert acquire_slot(tmp_cfg, "run-1") is True


def test_acquire_within_limit(tmp_cfg):
    assert acquire_slot(tmp_cfg, "run-1") is True
    assert acquire_slot(tmp_cfg, "run-2") is True


def test_acquire_exceeds_limit(tmp_cfg):
    acquire_slot(tmp_cfg, "run-1")
    acquire_slot(tmp_cfg, "run-2")
    assert acquire_slot(tmp_cfg, "run-3") is False


def test_release_frees_slot(tmp_cfg):
    acquire_slot(tmp_cfg, "run-1")
    acquire_slot(tmp_cfg, "run-2")
    release_slot(tmp_cfg, "run-1")
    assert acquire_slot(tmp_cfg, "run-3") is True


def test_release_missing_slot_is_noop(tmp_cfg):
    acquire_slot(tmp_cfg, "run-1")
    release_slot(tmp_cfg, "nonexistent")  # should not raise
    assert active_count(tmp_cfg) == 1


def test_active_count_empty(tmp_cfg):
    assert active_count(tmp_cfg) == 0


def test_active_count_after_acquire(tmp_cfg):
    acquire_slot(tmp_cfg, "run-1")
    assert active_count(tmp_cfg) == 1


def test_disabled_always_allows(tmp_path):
    cfg = ConcurrencyConfig(max_instances=1, state_dir=str(tmp_path), job_name="j", enabled=False)
    assert acquire_slot(cfg, "run-1") is True
    assert acquire_slot(cfg, "run-2") is True


def test_dead_pid_slot_pruned(tmp_cfg):
    path = _state_path(tmp_cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write a slot with a PID that definitely does not exist
    path.write_text(json.dumps([{"run_id": "ghost", "pid": 99999999, "started_at": 0.0}]))
    # Should be pruned, so acquiring should succeed even at max_instances=2
    assert acquire_slot(tmp_cfg, "run-live") is True
