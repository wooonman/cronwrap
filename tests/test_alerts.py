"""Tests for cronwrap.alerts module."""

import pytest
from unittest.mock import patch, MagicMock
from cronwrap.alerts import AlertConfig, send_email_alert, maybe_alert


def make_config(**kwargs):
    defaults = dict(
        email_to="ops@example.com",
        email_from="cronwrap@example.com",
        smtp_host="localhost",
        smtp_port=25,
    )
    defaults.update(kwargs)
    return AlertConfig(**defaults)


def test_send_email_missing_config_skips():
    config = AlertConfig()  # no email_to / email_from
    result = send_email_alert(config, "backup", "something went wrong")
    assert result is False


@patch("cronwrap.alerts.smtplib.SMTP")
def test_send_email_success(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value = mock_server

    config = make_config()
    result = send_email_alert(config, "backup", "disk full", exit_code=1)

    assert result is True
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


@patch("cronwrap.alerts.smtplib.SMTP")
def test_send_email_with_auth(mock_smtp_cls):
    mock_server = MagicMock()
    mock_smtp_cls.return_value = mock_server

    config = make_config(smtp_user="user", smtp_password="pass")
    result = send_email_alert(config, "myjob", "failed")

    assert result is True
    mock_server.login.assert_called_once_with("user", "pass")


@patch("cronwrap.alerts.smtplib.SMTP")
def test_send_email_smtp_error_returns_false(mock_smtp_cls):
    mock_smtp_cls.side_effect = ConnectionRefusedError("no server")

    config = make_config()
    result = send_email_alert(config, "myjob", "failed")

    assert result is False


@patch("cronwrap.alerts.send_email_alert")
def test_maybe_alert_calls_email_when_configured(mock_send):
    config = make_config()
    maybe_alert(config, "job", "error output", exit_code=2)
    mock_send.assert_called_once_with(config, "job", "error output", 2)


@patch("cronwrap.alerts.send_email_alert")
def test_maybe_alert_skips_when_no_email(mock_send):
    config = AlertConfig()  # no email_to
    maybe_alert(config, "job", "error output")
    mock_send.assert_not_called()
