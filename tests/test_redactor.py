"""Tests for cronwrap.redactor."""

import pytest
from cronwrap.redactor import RedactorConfig, redact, redact_result, describe_redactor


def make_config(**kwargs) -> RedactorConfig:
    return RedactorConfig(**kwargs)


def test_redact_no_patterns_returns_original():
    cfg = make_config()
    assert redact("hello secret world", cfg) == "hello secret world"


def test_redact_single_pattern():
    cfg = make_config(patterns=[r"secret"])
    assert redact("hello secret world", cfg) == "hello ***REDACTED*** world"


def test_redact_multiple_patterns():
    cfg = make_config(patterns=[r"password=\S+", r"token=\S+"])
    text = "password=abc123 and token=xyz789 here"
    result = redact(text, cfg)
    assert "abc123" not in result
    assert "xyz789" not in result
    assert "***REDACTED***" in result


def test_redact_case_insensitive_default():
    cfg = make_config(patterns=[r"secret"])
    assert redact("SECRET value", cfg) == "***REDACTED*** value"


def test_redact_case_sensitive():
    cfg = make_config(patterns=[r"secret"], case_sensitive=True)
    assert redact("SECRET value", cfg) == "SECRET value"
    assert redact("secret value", cfg) == "***REDACTED*** value"


def test_redact_custom_replacement():
    cfg = make_config(patterns=[r"\d{4}-\d{4}-\d{4}-\d{4}"], replacement="[CARD]")
    assert redact("card: 1234-5678-9012-3456", cfg) == "card: [CARD]"


def test_redact_empty_string():
    cfg = make_config(patterns=[r"secret"])
    assert redact("", cfg) == ""


def test_redact_invalid_pattern_skipped():
    cfg = make_config(patterns=[r"[invalid", r"secret"])
    assert redact("secret here", cfg) == "***REDACTED*** here"


def test_redact_result_both_streams():
    cfg = make_config(patterns=[r"password"])
    out, err = redact_result("password=123", "error: bad password", cfg)
    assert "password" not in out
    assert "password" not in err


def test_redact_result_none_inputs():
    cfg = make_config(patterns=[r"secret"])
    out, err = redact_result(None, None, cfg)
    assert out == ""
    assert err == ""


def test_from_dict_full():
    cfg = RedactorConfig.from_dict({
        "patterns": [r"api_key=\S+"],
        "replacement": "<hidden>",
        "case_sensitive": True,
    })
    assert cfg.patterns == [r"api_key=\S+"]
    assert cfg.replacement == "<hidden>"
    assert cfg.case_sensitive is True


def test_from_dict_defaults():
    cfg = RedactorConfig.from_dict({})
    assert cfg.patterns == []
    assert cfg.replacement == "***REDACTED***"
    assert cfg.case_sensitive is False


def test_enabled():
    assert not make_config().enabled()
    assert make_config(patterns=[r"secret"]).enabled()


def test_describe_redactor_disabled():
    assert describe_redactor(make_config()) == "redaction disabled"


def test_describe_redactor_enabled():
    cfg = make_config(patterns=[r"secret", r"token"])
    desc = describe_redactor(cfg)
    assert "2 pattern" in desc
    assert "***REDACTED***" in desc
