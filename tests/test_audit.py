"""Tests for cronwrap.audit and cronwrap.middleware_audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwrap.audit import (
    AuditEntry,
    make_audit_entry,
    read_audit,
    record_audit,
)
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_audit import AuditMiddleware, attach_audit_middleware


@pytest.fixture()
def audit_dir(tmp_path: Path) -> str:
    return str(tmp_path / "audit")


def _entry(run_id: str = "abc", exit_code: int = 0) -> AuditEntry:
    return make_audit_entry(
        run_id=run_id,
        command="echo hello",
        exit_code=exit_code,
        retries=0,
        tags=["nightly"],
    )


# ---------------------------------------------------------------------------
# AuditEntry / make_audit_entry
# ---------------------------------------------------------------------------

def test_make_audit_entry_success():
    e = _entry(exit_code=0)
    assert e.success is True
    assert e.exit_code == 0
    assert e.command == "echo hello"
    assert "nightly" in e.tags
    assert e.host  # non-empty
    assert e.user  # non-empty


def test_make_audit_entry_failure():
    e = _entry(exit_code=1)
    assert e.success is False


def test_as_dict_roundtrip():
    e = _entry()
    d = e.as_dict()
    assert d["run_id"] == "abc"
    restored = AuditEntry(**d)
    assert restored == e


# ---------------------------------------------------------------------------
# record_audit / read_audit
# ---------------------------------------------------------------------------

def test_record_and_read(audit_dir):
    e = _entry(run_id="r1")
    record_audit(e, audit_dir=audit_dir)
    entries = read_audit(audit_dir=audit_dir)
    assert len(entries) == 1
    assert entries[0].run_id == "r1"


def test_read_missing_returns_empty(audit_dir):
    entries = read_audit(audit_dir=audit_dir)
    assert entries == []


def test_multiple_entries_appended(audit_dir):
    for i in range(3):
        record_audit(_entry(run_id=str(i)), audit_dir=audit_dir)
    entries = read_audit(audit_dir=audit_dir)
    assert len(entries) == 3
    assert [e.run_id for e in entries] == ["0", "1", "2"]


# ---------------------------------------------------------------------------
# AuditMiddleware / attach_audit_middleware
# ---------------------------------------------------------------------------

class FakeContext:
    def __init__(self):
        self.run_id = "ctx-1"
        self.command = "ls -la"
        self.tags = ["daily"]
        self.started_at = None


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code
        self.retries = 2
        self.finished_at = None


def test_middleware_post_writes_entry(audit_dir):
    mw = AuditMiddleware(audit_dir=audit_dir)
    ctx = FakeContext()
    res = FakeResult(exit_code=0)
    mw.pre(ctx)
    mw.post(ctx, res)
    entries = read_audit(audit_dir=audit_dir)
    assert len(entries) == 1
    assert entries[0].run_id == "ctx-1"
    assert entries[0].retries == 2
    assert entries[0].success is True


def test_attach_audit_middleware_via_chain(audit_dir):
    chain = MiddlewareChain()
    attach_audit_middleware(chain, audit_dir=audit_dir)
    ctx = FakeContext()
    res = FakeResult(exit_code=1)
    chain.run_pre(ctx)
    chain.run_post(ctx, res)
    entries = read_audit(audit_dir=audit_dir)
    assert entries[0].success is False
