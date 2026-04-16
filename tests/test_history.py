"""Tests for cronwrap.history."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.history import get_history, summarize, print_history, RunSummary
from cronwrap.log_store import LogEntry, append_log


def make_entry(exit_code: int = 0, duration: float = 1.0) -> LogEntry:
    return LogEntry(
        timestamp="2024-01-01T00:00:00",
        command="echo hi",
        exit_code=exit_code,
        duration=duration,
        stdout="hi",
        stderr="",
        attempts=1,
    )


@pytest.fixture
def log_file(tmp_path):
    return tmp_path / "runs.jsonl"


def test_get_history_empty(log_file):
    assert get_history(log_file) == []


def test_get_history_limit(log_file):
    for _ in range(10):
        append_log(log_file, make_entry())
    result = get_history(log_file, limit=5)
    assert len(result) == 5


def test_summarize_all_success():
    entries = [make_entry(exit_code=0, duration=2.0) for _ in range(4)]
    s = summarize(entries)
    assert s.total == 4
    assert s.successes == 4
    assert s.failures == 0
    assert s.success_rate == 100.0
    assert s.avg_duration == pytest.approx(2.0)
    assert s.last_status == "success"


def test_summarize_mixed():
    entries = [make_entry(0), make_entry(1), make_entry(1)]
    s = summarize(entries)
    assert s.successes == 1
    assert s.failures == 2
    assert s.last_status == "failure"
    assert s.success_rate == pytest.approx(33.333, rel=1e-2)


def test_summarize_empty():
    s = summarize([])
    assert s.total == 0
    assert s.last_status is None
    assert s.success_rate == 0.0


def test_print_history_no_entries(log_file, capsys):
    print_history(log_file)
    out = capsys.readouterr().out
    assert "No history" in out


def test_print_history_with_entries(log_file, capsys):
    append_log(log_file, make_entry(exit_code=0, duration=0.5))
    append_log(log_file, make_entry(exit_code=1, duration=1.5))
    print_history(log_file)
    out = capsys.readouterr().out
    assert "OK" in out
    assert "FAIL" in out
