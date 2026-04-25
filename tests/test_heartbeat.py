"""Tests for cronwrap.heartbeat and cronwrap.middleware_heartbeat."""
from __future__ import annotations

import threading
from unittest.mock import patch, MagicMock

import pytest

from cronwrap.heartbeat import HeartbeatConfig, ping, ping_start, ping_finish, ping_loop
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_heartbeat import HeartbeatMiddleware, attach_heartbeat_middleware


# ---------------------------------------------------------------------------
# HeartbeatConfig
# ---------------------------------------------------------------------------

def test_config_disabled_when_no_url():
    cfg = HeartbeatConfig()
    assert not cfg.enabled


def test_config_enabled_with_url():
    cfg = HeartbeatConfig(url="https://hc-ping.example.com/abc")
    assert cfg.enabled


def test_from_dict_full():
    cfg = HeartbeatConfig.from_dict({
        "url": "https://example.com/ping",
        "interval_seconds": 10,
        "timeout_seconds": 3,
        "headers": {"X-Token": "secret"},
    })
    assert cfg.url == "https://example.com/ping"
    assert cfg.interval_seconds == 10.0
    assert cfg.timeout_seconds == 3.0
    assert cfg.headers == {"X-Token": "secret"}


def test_from_dict_defaults():
    cfg = HeartbeatConfig.from_dict({})
    assert cfg.url == ""
    assert cfg.interval_seconds == 0.0
    assert cfg.timeout_seconds == 5.0


# ---------------------------------------------------------------------------
# ping helpers
# ---------------------------------------------------------------------------

def test_ping_disabled_returns_false():
    cfg = HeartbeatConfig()
    assert ping(cfg) is False


def test_ping_success():
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_cm):
        assert ping(cfg) is True


def test_ping_url_error_returns_false():
    import urllib.error
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        assert ping(cfg) is False


def test_ping_start_appends_start_suffix():
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    captured = {}
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        return mock_cm

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        ping_start(cfg)
    assert captured["url"].endswith("/start")


def test_ping_finish_fail_suffix():
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    captured = {}
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        return mock_cm

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        ping_finish(cfg, success=False)
    assert captured["url"].endswith("/fail")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class FakeContext:
    pass


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code


def test_middleware_pre_post_calls_ping(tmp_path):
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    calls = []
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = MagicMock(return_value=False)

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return mock_cm

    mw = HeartbeatMiddleware(cfg)
    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        mw.pre(FakeContext())
        mw.post(FakeContext(), FakeResult(exit_code=0))

    assert any("start" in u for u in calls)
    assert any("finish" in u for u in calls)


def test_middleware_disabled_no_ping():
    cfg = HeartbeatConfig()  # no url
    mw = HeartbeatMiddleware(cfg)
    with patch("urllib.request.urlopen") as mock_open:
        mw.pre(FakeContext())
        mw.post(FakeContext(), FakeResult())
    mock_open.assert_not_called()


def test_attach_adds_to_chain():
    cfg = HeartbeatConfig(url="https://hc.example.com/abc")
    chain = MiddlewareChain()
    attach_heartbeat_middleware(chain, cfg)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
