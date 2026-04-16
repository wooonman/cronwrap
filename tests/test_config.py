"""Tests for cronwrap.config."""
import json
import os
import pytest

from cronwrap.config import CronwrapConfig, load_config


@pytest.fixture
def json_config(tmp_path):
    cfg = {
        "retries": 3,
        "timeout": 60,
        "log_file": "/tmp/cron.log",
        "alert_email": "ops@example.com",
        "slack_webhook_url": "http://slack",
        "generic_webhook_url": "http://hook",
        "notify_on_success": True,
        "notify_on_failure": True,
        "extra_webhook_headers": {"X-Key": "secret"},
    }
    p = tmp_path / "cronwrap.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_load_json_config(json_config):
    cfg = load_config(json_config)
    assert cfg.retries == 3
    assert cfg.timeout == 60
    assert cfg.log_file == "/tmp/cron.log"
    assert cfg.alert_email == "ops@example.com"
    assert cfg.slack_webhook_url == "http://slack"
    assert cfg.notify_on_success is True
    assert cfg.extra_webhook_headers == {"X-Key": "secret"}


def test_load_json_defaults(tmp_path):
    p = tmp_path / "minimal.json"
    p.write_text(json.dumps({}))
    cfg = load_config(str(p))
    assert cfg.retries == 0
    assert cfg.timeout is None
    assert cfg.notify_on_failure is True
    assert cfg.notify_on_success is False
    assert cfg.extra_webhook_headers == {}


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path.json")


def test_load_unsupported_format(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("retries: 1")
    with pytest.raises(ValueError, match="Unsupported"):
        load_config(str(p))


def test_cronwrap_config_defaults():
    cfg = CronwrapConfig()
    assert cfg.retries == 0
    assert cfg.timeout is None
    assert cfg.notify_on_failure is True
