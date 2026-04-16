"""Utilities for validating and describing cron schedule expressions."""
from dataclasses import dataclass
from typing import Optional
import re

CRON_FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]
CRON_FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


@dataclass
class CronExpression:
    raw: str
    fields: list
    valid: bool
    error: Optional[str] = None


def _validate_field(value: str, low: int, high: int) -> bool:
    if value == "*":
        return True
    if re.fullmatch(r"\*/\d+", value):
        step = int(value.split("/")[1])
        return step >= 1
    if re.fullmatch(r"\d+", value):
        return low <= int(value) <= high
    if re.fullmatch(r"\d+-\d+", value):
        a, b = map(int, value.split("-"))
        return low <= a <= b <= high
    if re.fullmatch(r"[\d,]+", value):
        return all(low <= int(v) <= high for v in value.split(","))
    return False


def parse_cron(expression: str) -> CronExpression:
    """Parse and validate a 5-field cron expression."""
    parts = expression.strip().split()
    if len(parts) != 5:
        return CronExpression(raw=expression, fields=[], valid=False,
                              error=f"Expected 5 fields, got {len(parts)}")
    for i, (part, (low, high)) in enumerate(zip(parts, CRON_FIELD_RANGES)):
        if not _validate_field(part, low, high):
            return CronExpression(raw=expression, fields=parts, valid=False,
                                  error=f"Invalid value '{part}' for field '{CRON_FIELD_NAMES[i]}'")
    return CronExpression(raw=expression, fields=parts, valid=True)


def describe_cron(expression: str) -> str:
    """Return a human-readable description of a cron expression."""
    parsed = parse_cron(expression)
    if not parsed.valid:
        return f"Invalid expression: {parsed.error}"
    minute, hour, dom, month, dow = parsed.fields
    parts = []
    parts.append(f"minute={minute}" if minute != "*" else "every minute")
    parts.append(f"hour={hour}" if hour != "*" else "every hour")
    if dom != "*":
        parts.append(f"day-of-month={dom}")
    if month != "*":
        parts.append(f"month={month}")
    if dow != "*":
        parts.append(f"day-of-week={dow}")
    return ", ".join(parts)
