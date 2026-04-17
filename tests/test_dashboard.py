"""Tests for cronwrap.dashboard"""
import pytest
from datetime import datetime
from cronwrap.metrics import RunMetric, record_metric
from cronwrap.dashboard import print_dashboard, _bar


@pytest.fixture
def metrics_dir(tmp_path):
    return str(tmp_path / "metrics")


def make_metric(job="myjob", exit_code=0, duration=1.0, retries=0, timed_out=False):
    return RunMetric(
        job_name=job,
        started_at=datetime.utcnow().isoformat(),
        duration_seconds=duration,
        exit_code=exit_code,
        retries=retries,
        timed_out=timed_out,
    )


def test_dashboard_no_metrics(metrics_dir, capsys):
    print_dashboard("ghost_job", base_dir=metrics_dir)
    out = capsys.readouterr().out
    assert "No metrics found" in out


def test_dashboard_with_metrics(metrics_dir, capsys):
    for i in range(3):
        record_metric(make_metric(exit_code=0, duration=float(i + 1)), base_dir=metrics_dir)
    record_metric(make_metric(exit_code=1, duration=2.0), base_dir=metrics_dir)
    print_dashboard("myjob", base_dir=metrics_dir)
    out = capsys.readouterr().out
    assert "myjob" in out
    assert "Success rate" in out
    assert "75.0%" in out


def test_dashboard_shows_timeout(metrics_dir, capsys):
    record_metric(make_metric(timed_out=True, exit_code=1), base_dir=metrics_dir)
    print_dashboard("myjob", base_dir=metrics_dir)
    out = capsys.readouterr().out
    assert "TIMEOUT" in out


def test_bar_full():
    assert _bar(10, 10) == "[" + "#" * 20 + "-" * 0 + "]"


def test_bar_empty():
    assert _bar(0, 10) == "[" + "-" * 20 + "]"


def test_bar_zero_total():
    assert _bar(0, 0) == "[" + "-" * 20 + "]"
