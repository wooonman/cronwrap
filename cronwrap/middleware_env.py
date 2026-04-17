"""Middleware that injects environment variables before running a command."""
from __future__ import annotations

from typing import Optional

from cronwrap.env import EnvConfig, build_env, redact_env
from cronwrap.middleware import MiddlewareChain


class EnvMiddleware:
    """Pre-hook that builds and stores the env dict on the context."""

    def __init__(self, config: EnvConfig) -> None:
        self.config = config

    def pre(self, context: dict) -> None:
        env = build_env(self.config)
        context["env"] = env
        context["env_redacted"] = redact_env(env, self.config.mask)

    def post(self, context: dict, result: object) -> None:
        # Nothing to do after run
        pass


def attach_env_middleware(
    chain: MiddlewareChain,
    config: Optional[EnvConfig] = None,
) -> EnvMiddleware:
    """Attach EnvMiddleware to a MiddlewareChain and return the middleware."""
    if config is None:
        config = EnvConfig()
    mw = EnvMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
    return mw
