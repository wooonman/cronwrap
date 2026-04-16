"""Tests for cron schedule parsing and description."""
import pytest
from cronwrap.schedule import parse_cron, describe_cron, CronExpression


def test_parse_valid_all_wildcards():
    result = parse_cron("* * * * *")
    assert result.valid is True
    assert result.fields == ["*", "*", "*", "*", "*"]


def test_parse_valid_specific_values():
    result = parse_cron("0 12 1 6 1")
    assert result.valid is True


def test_parse_valid_step():
    result = parse_cron("*/5 * * * *")
    assert result.valid is True


def test_parse_valid_range():
    result = parse_cron("0 9-17 * * 1-5")
    assert result.valid is True


def test_parse_valid_list():
    result = parse_cron("0 8,12,18 * * *")
    assert result.valid is True


def test_parse_wrong_field_count():
    result = parse_cron("* * * *")
    assert result.valid is False
    assert "5 fields" in result.error


def test_parse_out_of_range_minute():
    result = parse_cron("60 * * * *")
    assert result.valid is False
    assert "minute" in result.error


def test_parse_out_of_range_hour():
    result = parse_cron("0 25 * * *")
    assert result.valid is False
    assert "hour" in result.error


def test_describe_all_wildcards():
    desc = describe_cron("* * * * *")
    assert "every minute" in desc
    assert "every hour" in desc


def test_describe_specific():
    desc = describe_cron("30 6 * * *")
    assert "minute=30" in desc
    assert "hour=6" in desc


def test_describe_invalid():
    desc = describe_cron("bad expression")
    assert "Invalid" in desc
