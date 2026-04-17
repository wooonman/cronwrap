"""Middleware that attaches tags to runs and persists them."""
from __future__ import annotations
from typing import List, Optional
from cronwrap.middleware import MiddlewareChain
from cronwrap.tags import TaggedRun, save_tagged_run, parse_tags


class TagsMiddleware:
    def __init__(self, tags: List[str], tags_file: Optional[str] = None):
        self.tags = tags
        self.tags_file = tags_file
        self._run_id: Optional[str] = None
        self._command: Optional[str] = None

    def pre(self, context: dict) -> None:
        self._run_id = context.get("run_id", "unknown")
        self._command = context.get("command", "")

    def post(self, context: dict, result) -> None:
        run = TaggedRun(
            run_id=self._run_id or "unknown",
            command=self._command or "",
            tags=self.tags,
            exit_code=getattr(result, "exit_code", None),
        )
        kwargs = {"path": self.tags_file} if self.tags_file else {}
        save_tagged_run(run, **kwargs)


def attach_tags_middleware(
    chain: MiddlewareChain,
    tags_raw: Optional[str] = None,
    tags: Optional[List[str]] = None,
    tags_file: Optional[str] = None,
) -> TagsMiddleware:
    resolved = tags if tags is not None else parse_tags(tags_raw)
    mw = TagsMiddleware(tags=resolved, tags_file=tags_file)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
