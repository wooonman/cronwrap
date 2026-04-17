"""Tests for cronwrap.env."""
import os
import pytest

from cronwrap.env import (
    EnvConfig,
    build_env,
    redact_env,
    env_from_dict,
    describe_env,
)


def test_build_env_inherits_os_env():
    config = EnvConfig(vars={"FOO": "bar"}, inherit=True)
    result = build_env(config)
    assert result["FOO"] == "bar"
    # Should contain at least one OS env var
    assert len(result) > 1


def test_build_env_no_inherit():
    config = EnvConfig(vars={"ONLY": "this"}, inherit=False)
    result = build_env(config)
    assert result == {"ONLY": "this"}


def test_build_env_override_os_var():
    os.environ["_CW_TEST_VAR"] = "original"
    config = EnvConfig(vars={"_CW_TEST_VAR": "overridden"}, inherit=True)
    result = build_env(config)
    assert result["_CW_TEST_VAR"] == "overridden"
    del os.environ["_CW_TEST_VAR"]


def test_redact_env_masks_keys():
    env = {"SECRET": "abc123", "USER": "alice"}
    result = redact_env(env, mask=["SECRET"])
    assert result["SECRET"] == "***"
    assert result["USER"] == "alice"


def test_redact_env_missing_key_ok():
    env = {"USER": "alice"}
    result = redact_env(env, mask=["MISSING"])
    assert "MISSING" not in result


def test_redact_env_does_not_mutate_original():
    env = {"SECRET": "real"}
    redact_env(env, mask=["SECRET"])
    assert env["SECRET"] == "real"


def test_env_from_dict_full():
    data = {"vars": {"A": "1"}, "inherit": False, "mask": ["A"]}
    cfg = env_from_dict(data)
    assert cfg.vars == {"A": "1"}
    assert cfg.inherit is False
    assert cfg.mask == ["A"]


def test_env_from_dict_defaults():
    cfg = env_from_dict({})
    assert cfg.inherit is True
    assert cfg.vars == {}
    assert cfg.mask == []


def test_describe_env_inherit():
    cfg = EnvConfig(vars={"X": "1"}, inherit=True, mask=["X"])
    desc = describe_env(cfg)
    assert "inherits" in desc
    assert "1 variable" in desc
    assert "masks" in desc


def test_describe_env_isolated():
    cfg = EnvConfig(inherit=False)
    desc = describe_env(cfg)
    assert "isolated" in desc
