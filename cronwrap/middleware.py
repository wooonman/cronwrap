"""Pre/post run middleware hooks for cronwrap."""

from typing import Callable, List

from cronwrap.context import RunContext
from cronwrap.runner import RunResult

PreHook = Callable[[RunContext], None]
PostHook = Callable[[RunContext, RunResult], None]


class MiddlewareChain:
    def __init__(self):
        self._pre: List[PreHook] = []
        self._post: List[PostHook] = []

    def add_pre(self, fn: PreHook) -> "MiddlewareChain":
        self._pre.append(fn)
        return self

    def add_post(self, fn: PostHook) -> "MiddlewareChain":
        self._post.append(fn)
        return self

    def run_pre(self, ctx: RunContext) -> None:
        for fn in self._pre:
            fn(ctx)

    def run_post(self, ctx: RunContext, result: RunResult) -> None:
        for fn in self._post:
            fn(ctx, result)


def lock_pre_hook(ctx: RunContext) -> None:
    """Acquire a lock before running; raises if already locked."""
    from cronwrap.lock import acquire_lock
    if ctx.dry_run:
        return
    path = acquire_lock(ctx.job_name, ctx.lock_dir)
    if path is None:
        raise RuntimeError(f"Job '{ctx.job_name}' is already running (lock held).")
    ctx._lock_path = path  # type: ignore[attr-defined]


def lock_post_hook(ctx: RunContext, result: RunResult) -> None:
    """Release the lock after running."""
    from cronwrap.lock import release_lock
    lock_path = getattr(ctx, "_lock_path", None)
    if lock_path is not None:
        release_lock(lock_path)


def build_default_chain() -> MiddlewareChain:
    chain = MiddlewareChain()
    chain.add_pre(lock_pre_hook)
    chain.add_post(lock_post_hook)
    return chain
