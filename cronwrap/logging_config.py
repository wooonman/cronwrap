import logging
import json
import sys
from datetime import datetime
from typing import Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj)


def get_logger(
    name: str = "cronwrap",
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    handler: logging.Handler
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    if json_output:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )

    logger.addHandler(handler)
    return logger


def log_run_result(logger: logging.Logger, result, command: str) -> None:
    """Log a RunResult object from runner.py."""
    extra = {
        "command": command,
        "exit_code": result.exit_code,
        "retries": result.retries,
        "duration_seconds": round(result.duration, 3),
    }
    if result.success:
        logger.info("Command succeeded", extra={"extra": extra})
    else:
        logger.error(
            f"Command failed: {result.stderr or result.stdout or 'no output'}",
            extra={"extra": extra},
        )
