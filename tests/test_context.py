"""Tests for cronwrap.context"""

import os
from datetime import timezone

from cronwrap.context import RunContext, make_context


def test_run_context_defaults():
    ctx = RunContext(job_name="backup", command="tar -czf /tmp/x.tgz /data")
    assert ctx.job_name == "backup"
    assert ctx.pid == os.getpid()
    assert ctx.started_at.tzinfo == timezone.utc
    assert ctx.hostname != ""
    assert ctx.dry_run is False


def test_run_id_auto_generated():
    ctx = RunContext(job_name="myjob", command="echo hi")
    assert ctx.run_id.startswith("myjob-")
    assert str(os.getpid()) in ctx.run_id


def test_run_id_custom():
    ctx = RunContext(job_name="myjob", command="echo hi", run_id="custom-123")
    assert ctx.run_id == "custom-123"


def test_as_dict_keys():
    ctx = make_context("sync", "rsync -a /src /dst")
    d = ctx.as_dict()
    assert set(d.keys()) == {"job_name", "command", "started_at", "hostname", "pid", "run_id"}


def test_as_dict_values():
    ctx = make_context("sync", "rsync -a /src /dst")
    d = ctx.as_dict()
    assert d["job_name"] == "sync"
    assert d["command"] == "rsync -a /src /dst"
    assert "T" in d["started_at"]  # ISO format


def test_make_context_overrides():
    ctx = make_context("job", "cmd", dry_run=True, lock_dir="/var/lock")
    assert ctx.dry_run is True
    assert ctx.lock_dir == "/var/lock"
