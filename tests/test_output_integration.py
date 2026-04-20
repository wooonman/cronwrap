"""Integration: OutputMiddleware wired into a MiddlewareChain."""
from pathlib import Path

from cronwrap.middleware import MiddlewareChain
from cronwrap.output import OutputConfig, load_stored_output
from cronwrap.middleware_output import attach_output_middleware


class FakeContext:
    def __init__(self, run_id="int-run-1"):
        self.run_id = run_id


class FakeResult:
    def __init__(self, stdout="", stderr="", exit_code=0):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.output_truncated = False
        self.output_stored_path = None


def test_full_pipeline_no_store():
    chain = MiddlewareChain()
    attach_output_middleware(chain, OutputConfig(max_bytes=10000))

    ctx = FakeContext()
    result = FakeResult(stdout="all good", stderr="minor warning")

    chain.run_pre(ctx)
    chain.run_post(ctx, result)

    assert result.stdout == "all good"
    assert result.stderr == "minor warning"
    assert result.output_truncated is False
    assert result.output_stored_path is None


def test_full_pipeline_with_store_and_truncation(tmp_path):
    cfg = OutputConfig(max_bytes=10, store_dir=str(tmp_path))
    chain = MiddlewareChain()
    attach_output_middleware(chain, cfg)

    ctx = FakeContext(run_id="int-trunc")
    result = FakeResult(stdout="this is definitely more than ten bytes", stderr="")

    chain.run_pre(ctx)
    chain.run_post(ctx, result)

    assert result.output_truncated is True
    stored = load_stored_output(str(tmp_path), "int-trunc")
    assert stored is not None
    assert "...[truncated]" in stored


def test_multiple_middleware_order(tmp_path):
    """Output middleware plays nicely alongside other post hooks."""
    log = []

    chain = MiddlewareChain()
    chain.add_post(lambda ctx, res: log.append("before"))
    attach_output_middleware(chain, OutputConfig())
    chain.add_post(lambda ctx, res: log.append("after"))

    ctx = FakeContext()
    result = FakeResult(stdout="x", stderr="")
    chain.run_pre(ctx)
    chain.run_post(ctx, result)

    assert log == ["before", "after"]
    assert result.output_truncated is False
