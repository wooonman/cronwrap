"""Tests for cronwrap.checkpoint and cronwrap.middleware_checkpoint."""

from __future__ import annotations

import time

import pytest

from cronwrap.checkpoint import (
    Checkpoint,
    checkpoint_age_seconds,
    clear_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_checkpoint import CheckpointMiddleware, attach_checkpoint_middleware


@pytest.fixture()
def cp_dir(tmp_path):
    return str(tmp_path / "checkpoints")


def test_save_and_load_roundtrip(cp_dir):
    cp = Checkpoint(job_id="myjob", state={"step": 3}, attempt=2)
    save_checkpoint(cp, cp_dir)
    loaded = load_checkpoint("myjob", cp_dir)
    assert loaded is not None
    assert loaded.job_id == "myjob"
    assert loaded.state == {"step": 3}
    assert loaded.attempt == 2


def test_load_missing_returns_none(cp_dir):
    assert load_checkpoint("nonexistent", cp_dir) is None


def test_clear_removes_file(cp_dir):
    cp = Checkpoint(job_id="toclean")
    save_checkpoint(cp, cp_dir)
    assert clear_checkpoint("toclean", cp_dir) is True
    assert load_checkpoint("toclean", cp_dir) is None


def test_clear_missing_returns_false(cp_dir):
    assert clear_checkpoint("ghost", cp_dir) is False


def test_checkpoint_age(cp_dir):
    cp = Checkpoint(job_id="aged", saved_at=time.time() - 10)
    age = checkpoint_age_seconds(cp)
    assert 9 < age < 12


def test_as_dict_keys():
    cp = Checkpoint(job_id="j", state={"k": "v"}, attempt=1)
    d = cp.as_dict()
    assert set(d.keys()) == {"job_id", "state", "saved_at", "attempt"}


class FakeContext:
    pass


class FakeResult:
    def __init__(self, exit_code: int):
        self.exit_code = exit_code


def test_middleware_pre_creates_checkpoint(cp_dir):
    ctx = FakeContext()
    mw = CheckpointMiddleware(job_id="job1", directory=cp_dir)
    mw.pre(ctx)
    assert isinstance(ctx.checkpoint, Checkpoint)
    assert ctx.checkpoint.job_id == "job1"


def test_middleware_pre_restores_existing(cp_dir):
    save_checkpoint(Checkpoint(job_id="job2", state={"x": 99}, attempt=3), cp_dir)
    ctx = FakeContext()
    mw = CheckpointMiddleware(job_id="job2", directory=cp_dir)
    mw.pre(ctx)
    assert ctx.checkpoint.attempt == 3
    assert ctx.checkpoint.state == {"x": 99}


def test_middleware_post_success_clears(cp_dir):
    ctx = FakeContext()
    ctx.checkpoint = Checkpoint(job_id="job3", attempt=1)
    save_checkpoint(ctx.checkpoint, cp_dir)
    mw = CheckpointMiddleware(job_id="job3", directory=cp_dir)
    mw.post(ctx, FakeResult(exit_code=0))
    assert load_checkpoint("job3", cp_dir) is None


def test_middleware_post_failure_increments_attempt(cp_dir):
    ctx = FakeContext()
    ctx.checkpoint = Checkpoint(job_id="job4", attempt=0)
    mw = CheckpointMiddleware(job_id="job4", directory=cp_dir)
    mw.post(ctx, FakeResult(exit_code=1))
    loaded = load_checkpoint("job4", cp_dir)
    assert loaded is not None
    assert loaded.attempt == 1


def test_attach_adds_to_chain(cp_dir):
    chain = MiddlewareChain()
    mw = attach_checkpoint_middleware(chain, job_id="chained", directory=cp_dir)
    assert isinstance(mw, CheckpointMiddleware)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
