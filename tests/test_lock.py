"""Tests for cronwrap.lock"""

import os
from pathlib import Path

import pytest

from cronwrap.lock import acquire_lock, release_lock, read_lock


@pytest.fixture
def tmp_lock_dir(tmp_path):
    return str(tmp_path)


def test_acquire_lock_creates_file(tmp_lock_dir):
    path = acquire_lock("myjob", tmp_lock_dir)
    assert path is not None
    assert path.exists()
    release_lock(path)


def test_acquire_lock_blocked_by_existing(tmp_lock_dir):
    path = acquire_lock("myjob", tmp_lock_dir)
    assert path is not None
    # Second acquire should fail (same PID is alive)
    second = acquire_lock("myjob", tmp_lock_dir)
    assert second is None
    release_lock(path)


def test_release_lock_removes_file(tmp_lock_dir):
    path = acquire_lock("myjob", tmp_lock_dir)
    assert path.exists()
    release_lock(path)
    assert not path.exists()


def test_release_lock_missing_file_ok(tmp_lock_dir):
    path = Path(tmp_lock_dir) / "cronwrap_ghost.lock"
    release_lock(path)  # Should not raise


def test_stale_lock_overwritten(tmp_lock_dir):
    path = Path(tmp_lock_dir) / "cronwrap_myjob.lock"
    # Write a lock with a dead PID
    path.write_text("99999999,1234567890.0,myjob")
    result = acquire_lock("myjob", tmp_lock_dir)
    assert result is not None
    content = result.read_text()
    assert str(os.getpid()) in content
    release_lock(result)


def test_read_lock_returns_info(tmp_lock_dir):
    path = acquire_lock("readjob", tmp_lock_dir)
    info = read_lock("readjob", tmp_lock_dir)
    assert info is not None
    assert info.pid == os.getpid()
    assert info.job_name == "readjob"
    release_lock(path)


def test_read_lock_missing_returns_none(tmp_lock_dir):
    info = read_lock("nonexistent", tmp_lock_dir)
    assert info is None
