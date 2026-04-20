"""Tests for cronwrap.middleware_output."""
import pytest
from pathlib import Path

from cronwrap.middleware import MiddlewareChain
from cronwrap.output import OutputConfig
from cronwrap.middleware_output import OutputMiddleware, attach_output_middleware


class FakeContext:
    def __init__(self, run_id="run-abc"):
        self.run_id = run_id


class FakeResult:
    def __init__(self, stdout="", stderr="", exit_code=0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.output_truncated = False
        self.output_stored_path = None


# --- OutputMiddleware.pre is a no-op ---

def test_pre_is_noop():
    mw = OutputMiddleware(OutputConfig())
    ctx = FakeContext()
    mw.pre(ctx)  # should not raise


# --- post processes output ---

def test_post_sets_truncated_false_for_short_output():
    mw = OutputMiddleware(OutputConfig(max_bytes=10000))
    ctx = FakeContext()
    result = FakeResult(stdout="hello", stderr="world")
    mw.post(ctx, result)
    assert result.output_truncated is False


def test_post_sets_truncated_true_when_over_limit():
    mw = OutputMiddleware(OutputConfig(max_bytes=5))
    ctx = FakeContext()
    result = FakeResult(stdout="hello world this is long", stderr="")
    mw.post(ctx, result)
    assert result.output_truncated is True


def test_post_excludes_stderr_when_configured():
    mw = OutputMiddleware(OutputConfig(include_stderr=False))
    ctx = FakeContext()
    result = FakeResult(stdout="out", stderr="err")
    mw.post(ctx, result)
    assert result.stderr == ""


def test_post_stores_file(tmp_path):
    cfg = OutputConfig(store_dir=str(tmp_path))
    mw = OutputMiddleware(cfg)
    ctx = FakeContext(run_id="run-999")
    result = FakeResult(stdout="stored output", stderr="")
    mw.post(ctx, result)
    assert result.output_stored_path is not None
    assert Path(result.output_stored_path).read_text() == "stored output"


def test_post_no_store_without_run_id(tmp_path):
    cfg = OutputConfig(store_dir=str(tmp_path))
    mw = OutputMiddleware(cfg)
    ctx = FakeContext(run_id=None)
    result = FakeResult(stdout="data", stderr="")
    mw.post(ctx, result)
    assert result.output_stored_path is None


# --- attach_output_middleware ---

def test_attach_registers_hooks():
    chain = MiddlewareChain()
    mw = attach_output_middleware(chain, OutputConfig())
    assert isinstance(mw, OutputMiddleware)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1


def test_attach_uses_default_config_when_none():
    chain = MiddlewareChain()
    mw = attach_output_middleware(chain)
    assert mw.config.max_bytes == 64 * 1024
