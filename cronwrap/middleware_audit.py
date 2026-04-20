"""Middleware that records an audit entry for every run."""
from __future__ import annotations

from cronwrap.audit import make_audit_entry, record_audit
from cronwrap.middleware import MiddlewareChain


class AuditMiddleware:
    """Records an AuditEntry after each command run."""

    def __init__(self, audit_dir: str | None = None) -> None:
        from cronwrap.audit import DEFAULT_AUDIT_DIR
        self.audit_dir = audit_dir or DEFAULT_AUDIT_DIR

    def pre(self, context: object) -> None:  # noqa: D401
        """Nothing to do before the run."""

    def post(self, context: object, result: object) -> None:
        """Write an audit entry using data from context and result."""
        run_id = getattr(context, "run_id", "unknown")
        command = getattr(context, "command", "")
        exit_code = getattr(result, "exit_code", -1)
        retries = getattr(result, "retries", 0)
        tags = list(getattr(context, "tags", []) or [])
        started_at = getattr(context, "started_at", None)
        finished_at = getattr(result, "finished_at", None)

        entry = make_audit_entry(
            run_id=str(run_id),
            command=command if isinstance(command, str) else " ".join(command),
            exit_code=exit_code,
            retries=retries,
            tags=tags,
            started_at=started_at,
            finished_at=finished_at,
        )
        record_audit(entry, audit_dir=self.audit_dir)


def attach_audit_middleware(
    chain: MiddlewareChain, audit_dir: str | None = None
) -> None:
    """Register AuditMiddleware on *chain*."""
    mw = AuditMiddleware(audit_dir=audit_dir)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
