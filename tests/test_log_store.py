import os
import pytest
from cronwrap.log_store import LogEntry, append_log, read_logs, tail_logs


@pytest.fixture
def tmp_log(tmp_path):
    return str(tmp_path / "cronwrap.log")


def make_entry(**kwargs):
    defaults = dict(
        command="echo hi", success=True, exit_code=0,
        retries=0, duration=0.5, stdout="hi", stderr=""
    )
    defaults.update(kwargs)
    return LogEntry(**defaults)


def test_append_and_read(tmp_log):
    entry = make_entry()
    append_log(tmp_log, entry)
    entries = read_logs(tmp_log)
    assert len(entries) == 1
    assert entries[0].command == "echo hi"
    assert entries[0].success is True


def test_multiple_entries(tmp_log):
    for i in range(5):
        append_log(tmp_log, make_entry(exit_code=i))
    entries = read_logs(tmp_log)
    assert len(entries) == 5
    assert [e.exit_code for e in entries] == list(range(5))


def test_read_missing_file(tmp_log):
    assert read_logs(tmp_log) == []


def test_tail_logs(tmp_log):
    for i in range(10):
        append_log(tmp_log, make_entry(retries=i))
    tail = tail_logs(tmp_log, n=3)
    assert len(tail) == 3
    assert tail[-1].retries == 9


def test_timestamp_auto_set():
    entry = make_entry()
    assert entry.timestamp.endswith("Z")
    assert len(entry.timestamp) > 10
