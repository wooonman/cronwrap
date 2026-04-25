"""Middleware that wires HeartbeatConfig into the MiddlewareChain."""
from __future__ import annotations

import threading
from cronwrap.heartbeat import HeartbeatConfig, ping_start, ping_finish, ping_loop
from cronwrap.middleware import MiddlewareChain


class HeartbeatMiddleware:
    def __init__(self, config: HeartbeatConfig) -> None:
        self.config = config
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def pre(self, context) -> None:
        if not self.config.enabled:
            return
        ping_start(self.config)
        if self.config.interval_seconds > 0:
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=ping_loop,
                args=(self.config, self._stop_event),
                daemon=True,
            )
            self._thread.start()

    def post(self, context, result) -> None:
        if not self.config.enabled:
            return
        if self._stop_event is not None:
            self._stop_event.set()
            if self._thread is not None:
                self._thread.join(timeout=2.0)
        ping_finish(self.config, success=(result.exit_code == 0))


def attach_heartbeat_middleware(
    chain: MiddlewareChain, config: HeartbeatConfig
) -> None:
    mw = HeartbeatMiddleware(config)
    chain.add_pre(mw.pre)
    chain.add_post(mw.post)
