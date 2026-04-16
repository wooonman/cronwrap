"""Tests for cronwrap.notify."""
from unittest.mock import patch, MagicMock
import pytest

from cronwrap.notify import NotifyConfig, send_slack, send_webhook, maybe_notify, _post_json


def make_mock_response(status=200):
    resp = MagicMock()
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_send_slack_success():
    with patch("urllib.request.urlopen", return_value=make_mock_response(200)) as mock_open:
        result = send_slack("http://fake-slack", "hello")
    assert result is True


def test_send_slack_failure_status():
    with patch("urllib.request.urlopen", return_value=make_mock_response(500)):
        result = send_slack("http://fake-slack", "hello")
    assert result is False


def test_send_webhook_with_extra_headers():
    with patch("urllib.request.urlopen", return_value=make_mock_response(200)):
        result = send_webhook("http://fake", {"key": "val"}, {"X-Token": "abc"})
    assert result is True


def test_post_json_url_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = _post_json("http://bad-url", {})
    assert result is False


def test_maybe_notify_skips_success_by_default():
    config = NotifyConfig(slack_webhook_url="http://slack", on_success=False)
    with patch("cronwrap.notify.send_slack") as mock_slack:
        maybe_notify(config, success=True, command="echo hi", output="hi", exit_code=0)
    mock_slack.assert_not_called()


def test_maybe_notify_calls_slack_on_failure():
    config = NotifyConfig(slack_webhook_url="http://slack", on_failure=True)
    with patch("cronwrap.notify.send_slack", return_value=True) as mock_slack:
        maybe_notify(config, success=False, command="bad cmd", output="err", exit_code=1)
    mock_slack.assert_called_once()


def test_maybe_notify_calls_webhook_on_failure():
    config = NotifyConfig(generic_webhook_url="http://hook", on_failure=True)
    with patch("cronwrap.notify.send_webhook", return_value=True) as mock_hook:
        maybe_notify(config, success=False, command="cmd", output="", exit_code=2)
    mock_hook.assert_called_once()
    payload = mock_hook.call_args[0][1]
    assert payload["exit_code"] == 2
    assert payload["success"] is False


def test_maybe_notify_on_success_flag():
    config = NotifyConfig(slack_webhook_url="http://slack", on_success=True)
    with patch("cronwrap.notify.send_slack", return_value=True) as mock_slack:
        maybe_notify(config, success=True, command="echo", output="ok", exit_code=0)
    mock_slack.assert_called_once()
