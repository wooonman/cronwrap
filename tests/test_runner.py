import pytest
from cronwrap.runner import run_command


def test_successful_command():
    result = run_command("echo hello")
    assert result.success is True
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.attempts == 1


def test_failing_command_no_retries():
    result = run_command("exit 1", retries=0)
    assert result.success is False
    assert result.returncode == 1
    assert result.attempts == 1


def test_retries_exhausted():
    result = run_command("exit 2", retries=2, retry_delay=0)
    assert result.success is False
    assert result.attempts == 3


def test_succeeds_on_retry(tmp_path):
    counter_file = tmp_path / "count.txt"
    counter_file.write_text("0")
    script = (
        f"count=$(cat {counter_file}); "
        f"echo $((count+1)) > {counter_file}; "
        f"[ $((count+1)) -ge 2 ]"
    )
    result = run_command(script, retries=3, retry_delay=0)
    assert result.success is True
    assert result.attempts == 2


def test_timeout_triggers():
    result = run_command("sleep 10", timeout=0.1)
    assert result.success is False
    assert result.stderr == "TimeoutExpired"
    assert result.returncode == -1


def test_duration_is_recorded():
    result = run_command("echo hi")
    assert result.duration >= 0.0


def test_stderr_captured():
    result = run_command("echo error_msg >&2; exit 1")
    assert "error_msg" in result.stderr
    assert result.success is False
