"""Tests for the CLI entry point."""
import pytest
from unittest.mock import patch, MagicMock
from cronwrap.cli import build_parser, main
from cronwrap.runner import RunResult


def make_result(exit_code=0, retries_used=0):
    return RunResult(
        exit_code=exit_code,
        stdout="out",
        stderr="",
        duration=0.1,
        retries_used=retries_used,
    )


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["echo", "hi"])
    assert args.retries == 0
    assert args.timeout is None
    assert args.job_name == "cronwrap"


def test_build_parser_custom_values():
    parser = build_parser()
    args = parser.parse_args(["--retries", "3", "--timeout", "30", "--job-name", "myjob", "echo"])
    assert args.retries == 3
    assert args.timeout == 30.0
    assert args.job_name == "myjob"


def test_main_success_exits_zero():
    with patch("cronwrap.cli.run_command", return_value=make_result(0)) as mock_run, \
         patch("cronwrap.cli.maybe_alert") as mock_alert:
        with pytest.raises(SystemExit) as exc:
            main(["echo", "hello"])
        assert exc.value.code == 0
        mock_run.assert_called_once()


def test_main_failure_exits_nonzero():
    with patch("cronwrap.cli.run_command", return_value=make_result(1)), \
         patch("cronwrap.cli.maybe_alert"):
        with pytest.raises(SystemExit) as exc:
            main(["false"])
        assert exc.value.code == 1


def test_main_no_command_exits():
    with pytest.raises(SystemExit):
        main([])


def test_main_writes_log_file(tmp_path):
    log_file = str(tmp_path / "run.jsonl")
    with patch("cronwrap.cli.run_command", return_value=make_result(0)), \
         patch("cronwrap.cli.maybe_alert"), \
         patch("cronwrap.cli.append_log") as mock_append:
        with pytest.raises(SystemExit):
            main(["--log-file", log_file, "echo", "hi"])
        mock_append.assert_called_once()
        entry = mock_append.call_args[0][1]
        assert entry.exit_code == 0
