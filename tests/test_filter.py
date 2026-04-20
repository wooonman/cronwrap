"""Tests for cronwrap.filter and cronwrap.middleware_filter."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from cronwrap.filter import FilterConfig, describe_filter, should_suppress
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_filter import FilterMiddleware, attach_filter_middleware


def make_result(exit_code: int = 0, stdout: str = "", stderr: str = ""):
    r = MagicMock()
    r.exit_code = exit_code
    r.stdout = stdout
    r.stderr = stderr
    return r


def test_suppress_on_success():
    cfg = FilterConfig(suppress_on_success=True)
    assert should_suppress(cfg, make_result(0)) is True
    assert should_suppress(cfg, make_result(1)) is False


def test_suppress_exit_codes():
    cfg = FilterConfig(suppress_exit_codes=[2, 3])
    assert should_suppress(cfg, make_result(2)) is True
    assert should_suppress(cfg, make_result(3)) is True
    assert should_suppress(cfg, make_result(1)) is False


def test_suppress_empty_output():
    cfg = FilterConfig(suppress_empty_output=True)
    assert should_suppress(cfg, make_result(0, stdout="", stderr="")) is True
    assert should_suppress(cfg, make_result(0, stdout="hello")) is False


def test_suppress_output_pattern():
    cfg = FilterConfig(suppress_output_patterns=[r"nothing to do"])
    assert should_suppress(cfg, make_result(0, stdout="nothing to do today")) is True
    assert should_suppress(cfg, make_result(0, stdout="something happened")) is False


def test_no_filters_never_suppresses():
    cfg = FilterConfig()
    assert should_suppress(cfg, make_result(1, stdout="output")) is False


def test_from_dict_full():
    cfg = FilterConfig.from_dict({
        "suppress_on_success": True,
        "suppress_exit_codes": [5],
        "suppress_output_patterns": ["skip"],
        "suppress_empty_output": True,
    })
    assert cfg.suppress_on_success is True
    assert cfg.suppress_exit_codes == [5]
    assert cfg.suppress_output_patterns == ["skip"]
    assert cfg.suppress_empty_output is True


def test_from_dict_defaults():
    cfg = FilterConfig.from_dict({})
    assert cfg.suppress_on_success is False
    assert cfg.suppress_exit_codes == []


def test_describe_filter_no_filters():
    assert describe_filter(FilterConfig()) == "no filters"


def test_describe_filter_combined():
    cfg = FilterConfig(suppress_on_success=True, suppress_exit_codes=[1, 2])
    desc = describe_filter(cfg)
    assert "suppress on success" in desc
    assert "1, 2" in desc


def test_middleware_sets_suppressed_true():
    cfg = FilterConfig(suppress_on_success=True)
    mw = FilterMiddleware(cfg)
    result = make_result(0)
    mw.post(object(), result)
    assert result.suppressed is True


def test_middleware_sets_suppressed_false():
    cfg = FilterConfig(suppress_on_success=True)
    mw = FilterMiddleware(cfg)
    result = make_result(1)
    mw.post(object(), result)
    assert result.suppressed is False


def test_attach_filter_middleware_registers_hooks():
    chain = MiddlewareChain()
    cfg = FilterConfig(suppress_on_success=True)
    attach_filter_middleware(chain, cfg)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1
