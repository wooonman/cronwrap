"""Middleware that captures and processes command output after a run."""
from __future__ import annotations

from cronwrap.middleware import MiddlewareChain
from cronwrap.output import OutputConfig, process_output


class OutputMiddleware:
    """Post-run middleware: processes stdout/stderr on the RunResult."""

    def __init__(self, config: OutputConfig) -> None:
        self.config = config

    def pre(self, context: object) -> None:  # noqa: ARG002
        pass

    def post(self, context: object, result: object) -> None:
        run_id = getattr(context, "run_id", None)
        stdout = getattr(result, "stdout", "") or ""
        stderr = getattr(result, "stderr", "") or ""

        captured = process_output(stdout, stderr, self.config, run_id=run_id)

        result.stdout = captured.stdout
        result.stderr = captured.stderr
        result.output_truncated = captured.truncated
        result.output_stored_path = captured.stored_path


def attach_output_middleware(
    chain: MiddlewareChain,
    config: OutputConfig | None = None,
) -> OutputMiddleware:
    """Attach an OutputMiddleware to *chain* and return it."""
    mw = OutputMiddleware(config or OutputConfig())
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
