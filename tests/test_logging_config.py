import logging
import json
import pytest
from cronwrap.logging_config import get_logger, JsonFormatter, log_run_result


class FakeResult:
    def __init__(self, success, exit_code, retries, duration, stdout="", stderr=""):
        self.success = success
        self.exit_code = exit_code
        self.retries = retries
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr


def test_get_logger_returns_logger():
    logger = get_logger("test_basic", level="DEBUG")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.DEBUG


def test_get_logger_idempotent():
    l1 = get_logger("test_idem")
    l2 = get_logger("test_idem")
    assert l1 is l2
    assert len(l1.handlers) == 1


def test_json_formatter_output():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="hello world", args=(), exc_info=None
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
    assert "timestamp" in data


def test_log_run_result_success(caplog):
    logger = get_logger("test_run_success_log", level="INFO")
    result = FakeResult(success=True, exit_code=0, retries=0, duration=1.23)
    with caplog.at_level(logging.INFO, logger="test_run_success_log"):
        log_run_result(logger, result, "echo hi")
    assert any("succeeded" in r.message for r in caplog.records)


def test_log_run_result_failure(caplog):
    logger = get_logger("test_run_fail_log", level="ERROR")
    result = FakeResult(success=False, exit_code=1, retries=2, duration=0.5, stderr="oops")
    with caplog.at_level(logging.ERROR, logger="test_run_fail_log"):
        log_run_result(logger, result, "bad-cmd")
    assert any("failed" in r.message for r in caplog.records)
