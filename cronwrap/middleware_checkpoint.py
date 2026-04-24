"""Middleware that saves/restores a checkpoint around each run."""

from __future__ import annotations

from cronwrap.checkpoint import Checkpoint, clear_checkpoint, load_checkpoint, save_checkpoint
from cronwrap.middleware import MiddlewareChain


class CheckpointMiddleware:
    """Pre: restore any existing checkpoint onto the context.
    Post: on success clear it; on failure save updated attempt count."""

    def __init__(self, job_id: str, directory: str = "/tmp/cronwrap/checkpoints") -> None:
        self.job_id = job_id
        self.directory = directory

    def pre(self, context: object) -> None:
        existing = load_checkpoint(self.job_id, self.directory)
        if existing is not None:
            context.checkpoint = existing  # type: ignore[attr-defined]
        else:
            context.checkpoint = Checkpoint(job_id=self.job_id)  # type: ignore[attr-defined]

    def post(self, context: object, result: object) -> None:
        exit_code = getattr(result, "exit_code", 1)
        cp: Checkpoint = getattr(context, "checkpoint", Checkpoint(job_id=self.job_id))
        if exit_code == 0:
            clear_checkpoint(self.job_id, self.directory)
        else:
            cp.attempt += 1
            save_checkpoint(cp, self.directory)


def attach_checkpoint_middleware(
    chain: MiddlewareChain,
    job_id: str,
    directory: str = "/tmp/cronwrap/checkpoints",
) -> CheckpointMiddleware:
    mw = CheckpointMiddleware(job_id=job_id, directory=directory)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
