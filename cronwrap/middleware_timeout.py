"""Middleware that enforces per-run timeout via TimeoutConfig."""
from cronwrap.middleware import MiddlewareChain
from cronwrap.timeout import TimeoutConfig, TimeoutExpired, timeout_guard, describe_timeout
from cronwrap.context import RunContext
import logging

logger = logging.getLogger("cronwrap")


class TimeoutMiddleware:
    def __init__(self, config: TimeoutConfig):
        self.config = config
        self._ctx_manager = None

    def pre(self, context: RunContext) -> None:
        context.extra["timeout"] = describe_timeout(self.config)
        if self.config.enabled:
            logger.debug("timeout_guard entering: %s", describe_timeout(self.config))
            self._ctx_manager = timeout_guard(self.config)
            self._ctx_manager.__enter__()

    def post(self, context: RunContext, result) -> None:
        if self._ctx_manager is not None:
            try:
                self._ctx_manager.__exit__(None, None, None)
            except TimeoutExpired:
                pass
            finally:
                self._ctx_manager = None


def attach_timeout_middleware(chain: MiddlewareChain, config: TimeoutConfig) -> None:
    """Register timeout pre/post hooks on an existing MiddlewareChain."""
    mw = TimeoutMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
