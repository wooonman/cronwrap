"""Tests for cronwrap.metrics"""
import pytest
from datetime import datetime
from cronwrap.metrics import RunMetric, record_metric, read_metrics, aggregate


@pytest.fixture
def metrics_dir(tmp_path):
    return str(tmp_path / "metrics")


def make_metric(job="test_job", exit_code=0, duration=1.5, retries=0, timed_out=False):
    return RunMetric(
        job_name=job,
        started_at=datetime.utcnow().isoformat(),
        duration_seconds=duration,
        exit_code=exit_code,
        retries=retries,
        timed_out=timed_out,
    )


def test_record_and_read(metrics_dir):
    m = make_metric()
    record_metric(m, base_dir=metrics_dir)
    results = read_metrics("test_job", base_dir=metrics_dir)
    assert len(results) == 1
    assert results[0].job_name == "test_job"
    assert results[0].exit_code == 0


def test_read_missing_returns_empty(metrics_dir):
    results = read_metrics("nonexistent", base_dir=metrics_dir)
    assert results == []


def test_multiple_metrics(metrics_dir):
    for i in range(5):
        record_metric(make_metric(duration=float(i)), base_dir=metrics_dir)
    results = read_metrics("test_job", base_dir=metrics_dir)
    assert len(results) == 5


def test_read_limit(metrics_dir):
    for i in range(10):
        record_metric(make_metric(), base_dir=metrics_dir)
    results = read_metrics("test_job", base_dir=metrics_dir, limit=3)
    assert len(results) == 3


def test_aggregate_empty():
    result = aggregate([])
    assert result["count"] == 0


def test_aggregate_mixed(metrics_dir):
    metrics = [
        make_metric(exit_code=0, duration=2.0),
        make_metric(exit_code=1, duration=4.0),
        make_metric(exit_code=0, duration=3.0, retries=2),
    ]
    result = aggregate(metrics)
    assert result["count"] == 3
    assert result["success_count"] == 2
    assert result["failure_count"] == 1
    assert result["success_rate"] == 66.7
    assert result["total_retries"] == 2
    assert result["max_duration"] == 4.0
    assert result["min_duration"] == 2.0


def test_metric_success_property():
    assert make_metric(exit_code=0).success is True
    assert make_metric(exit_code=1).success is False
