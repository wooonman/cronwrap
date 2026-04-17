import time
import pytest
from cronwrap.ratelimit import RateLimitConfig, check_rate_limit, reset_rate_limit, runs_in_window


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


def test_first_run_allowed(tmp_dir):
    cfg = RateLimitConfig(max_runs=3, window_seconds=60)
    assert check_rate_limit("myjob", cfg, base_dir=tmp_dir) is True


def test_runs_within_limit(tmp_dir):
    cfg = RateLimitConfig(max_runs=3, window_seconds=60)
    for _ in range(3):
        result = check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    assert result is True


def test_exceeds_limit_blocked(tmp_dir):
    cfg = RateLimitConfig(max_runs=2, window_seconds=60)
    check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    assert check_rate_limit("myjob", cfg, base_dir=tmp_dir) is False


def test_reset_clears_state(tmp_dir):
    cfg = RateLimitConfig(max_runs=1, window_seconds=60)
    check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    assert check_rate_limit("myjob", cfg, base_dir=tmp_dir) is False
    reset_rate_limit("myjob", base_dir=tmp_dir)
    assert check_rate_limit("myjob", cfg, base_dir=tmp_dir) is True


def test_reset_missing_file_ok(tmp_dir):
    reset_rate_limit("nonexistent", base_dir=tmp_dir)  # should not raise


def test_runs_in_window_count(tmp_dir):
    cfg = RateLimitConfig(max_runs=10, window_seconds=60)
    check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    check_rate_limit("myjob", cfg, base_dir=tmp_dir)
    assert runs_in_window("myjob", 60, base_dir=tmp_dir) == 2


def test_different_jobs_independent(tmp_dir):
    cfg = RateLimitConfig(max_runs=1, window_seconds=60)
    check_rate_limit("job_a", cfg, base_dir=tmp_dir)
    assert check_rate_limit("job_b", cfg, base_dir=tmp_dir) is True


def test_old_timestamps_ignored(tmp_dir):
    import json
    from pathlib import Path
    from cronwrap.ratelimit import _rate_file

    cfg = RateLimitConfig(max_runs=1, window_seconds=10)
    path = _rate_file("myjob", tmp_dir)
    old_ts = time.time() - 100
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([old_ts]))
    assert check_rate_limit("myjob", cfg, base_dir=tmp_dir) is True
