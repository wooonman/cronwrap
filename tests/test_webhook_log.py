"""Tests for cronwrap.webhook_log and cronwrap.middleware_webhook_log."""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cronwrap.webhook_log import WebhookLogConfig, _build_payload, ship_log
from cronwrap.middleware_webhook_log import WebhookLogMiddleware


def make_result(exit_code=0, stdout="ok", stderr="", duration=1.2, command="echo hi"):
    return SimpleNamespace(
        exit_code=exit_code, stdout=stdout, stderr=stderr,
        duration=duration, command=command,
    )


def make_context(run_id="abc", job_name="myjob"):
    return SimpleNamespace(run_id=run_id, job_name=job_name)


# --- WebhookLogConfig ---

def test_from_dict_full():
    cfg = WebhookLogConfig.from_dict({
        "url": "https://example.com/log",
        "headers": {"X-Token": "secret"},
        "include_output": False,
        "timeout_seconds": 5,
        "on_success": False,
        "on_failure": True,
    })
    assert cfg.url == "https://example.com/log"
    assert cfg.headers == {"X-Token": "secret"}
    assert cfg.include_output is False
    assert cfg.timeout_seconds == 5
    assert cfg.on_success is False
    assert cfg.on_failure is True


def test_from_dict_defaults():
    cfg = WebhookLogConfig.from_dict({})
    assert cfg.url == ""
    assert cfg.include_output is True
    assert cfg.timeout_seconds == 10
    assert cfg.on_success is True
    assert cfg.on_failure is True


def test_enabled_with_url():
    assert WebhookLogConfig(url="https://x.com").enabled() is True


def test_not_enabled_without_url():
    assert WebhookLogConfig().enabled() is False


# --- _build_payload ---

def test_build_payload_includes_output():
    cfg = WebhookLogConfig(url="u", include_output=True)
    p = _build_payload(cfg, make_result(), make_context())
    assert p["stdout"] == "ok"
    assert p["run_id"] == "abc"
    assert p["success"] is True


def test_build_payload_excludes_output():
    cfg = WebhookLogConfig(url="u", include_output=False)
    p = _build_payload(cfg, make_result())
    assert "stdout" not in p
    assert "stderr" not in p


# --- ship_log ---

def test_ship_log_disabled_returns_false():
    assert ship_log(WebhookLogConfig(), make_result()) is False


def test_ship_log_success_skipped_when_on_success_false():
    cfg = WebhookLogConfig(url="https://x.com", on_success=False)
    assert ship_log(cfg, make_result(exit_code=0)) is False


def test_ship_log_failure_skipped_when_on_failure_false():
    cfg = WebhookLogConfig(url="https://x.com", on_failure=False)
    assert ship_log(cfg, make_result(exit_code=1)) is False


def test_ship_log_posts_and_returns_true():
    cfg = WebhookLogConfig(url="https://x.com/log")
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert ship_log(cfg, make_result()) is True


def test_ship_log_url_error_returns_false():
    import urllib.error
    cfg = WebhookLogConfig(url="https://x.com/log")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        assert ship_log(cfg, make_result()) is False


# --- WebhookLogMiddleware ---

def test_middleware_pre_is_noop():
    cfg = WebhookLogConfig(url="https://x.com")
    mw = WebhookLogMiddleware(cfg)
    ctx = make_context()
    mw.pre(ctx)  # should not raise


def test_middleware_post_sets_shipped_flag():
    cfg = WebhookLogConfig(url="https://x.com/log")
    mw = WebhookLogMiddleware(cfg)
    ctx = make_context()
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 201
    with patch("urllib.request.urlopen", return_value=mock_resp):
        mw.post(ctx, make_result())
    assert ctx.webhook_log_shipped is True


def test_middleware_post_disabled_no_flag():
    cfg = WebhookLogConfig()  # no url
    mw = WebhookLogMiddleware(cfg)
    ctx = make_context()
    mw.post(ctx, make_result())
    assert not hasattr(ctx, "webhook_log_shipped")
