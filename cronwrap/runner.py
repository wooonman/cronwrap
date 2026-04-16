import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration: float
    attempts: int
    success: bool


def run_command(
    command: str,
    retries: int = 0,
    retry_delay: float = 5.0,
    timeout: Optional[float] = None,
) -> RunResult:
    """
    Run a shell command with optional retry logic.

    Args:
        command: Shell command to execute.
        retries: Number of additional attempts after the first failure.
        retry_delay: Seconds to wait between retries.
        timeout: Optional timeout in seconds per attempt.

    Returns:
        RunResult with details of the final attempt.
    """
    attempts = 0
    max_attempts = retries + 1
    last_result = None

    for attempt in range(1, max_attempts + 1):
        attempts = attempt
        logger.info("Attempt %d/%d: %s", attempt, max_attempts, command)
        start = time.monotonic()

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.monotonic() - start
            last_result = RunResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                attempts=attempts,
                success=proc.returncode == 0,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            logger.warning("Attempt %d timed out after %.1fs", attempt, duration)
            last_result = RunResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr="TimeoutExpired",
                duration=duration,
                attempts=attempts,
                success=False,
            )

        if last_result.success:
            logger.info("Command succeeded on attempt %d", attempt)
            return last_result

        if attempt < max_attempts:
            logger.warning(
                "Attempt %d failed (rc=%d), retrying in %.1fs...",
                attempt,
                last_result.returncode,
                retry_delay,
            )
            time.sleep(retry_delay)

    logger.error("All %d attempt(s) failed for: %s", attempts, command)
    return last_result
