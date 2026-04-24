"""Middleware that enforces cooldown logic around job runs."""
from __future__ import annotations

import logging
from cronwrap.cooldown import CooldownConfig, check_cooldown, record_failure, clear_cooldown
from cronwrap.middleware import MiddlewareChain

logger = logging.getLogger(__name__)


class CooldownMiddleware:
    def __init__(self, cfg: CooldownConfig) -> None:
        self.cfg = cfg

    def pre(self, context: object) -> None:
        """Block execution if still in cooldown period."""
        allowed, remaining = check_cooldown(self.cfg)
        if not allowed:
            raise RuntimeError(
                f"[cooldown] Job '{self.cfg.job_id}' is cooling down. "
                f"{remaining:.1f}s remaining."
            )
        context.__dict__.setdefault("cooldown_cfg", self.cfg)

    def post(self, context: object, result: object) -> None:
        """Record failure or clear state depending on outcome."""
        exit_code = getattr(result, "exit_code", 0)
        if exit_code != 0:
            logger.debug("[cooldown] Recording failure for job '%s'", self.cfg.job_id)
            record_failure(self.cfg)
        else:
            clear_cooldown(self.cfg)


def attach_cooldown_middleware(chain: MiddlewareChain, cfg: CooldownConfig) -> None:
    mw = CooldownMiddleware(cfg)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
