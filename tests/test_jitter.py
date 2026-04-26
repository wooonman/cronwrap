"""Tests for cronwrap.jitter."""

import pytest
from cronwrap.jitter import JitterConfig


def make_config(strategy="none", max_ms=1000, seed=42):
    return JitterConfig(strategy=strategy, max_ms=max_ms, seed=seed)


def test_default_strategy_is_none():
    cfg = JitterConfig()
    assert cfg.strategy == "none"
    assert not cfg.enabled()


def test_from_dict_full():
    cfg = JitterConfig.from_dict({"strategy": "full", "max_ms": 500, "seed": 1})
    assert cfg.strategy == "full"
    assert cfg.max_ms == 500
    assert cfg.seed == 1


def test_from_dict_defaults():
    cfg = JitterConfig.from_dict({})
    assert cfg.strategy == "none"
    assert cfg.max_ms == 1000
    assert cfg.seed is None


def test_none_strategy_returns_base_unchanged():
    cfg = make_config(strategy="none")
    assert cfg.apply(2.0) == 2.0
    assert cfg.apply(0.0) == 0.0


def test_full_jitter_within_range():
    cfg = make_config(strategy="full", max_ms=2000, seed=7)
    for _ in range(20):
        result = cfg.apply(1.5)
        assert 0.0 <= result <= 2.0  # max(base_delay=1.5, cap=2.0)


def test_equal_jitter_at_least_half_base():
    cfg = make_config(strategy="equal", max_ms=1000, seed=99)
    base = 2.0
    for _ in range(20):
        result = cfg.apply(base)
        assert result >= base / 2.0
        assert result <= base


def test_decorrelated_jitter_at_least_base():
    cfg = make_config(strategy="decorrelated", max_ms=500, seed=3)
    base = 1.0
    for _ in range(20):
        result = cfg.apply(base)
        assert result >= base


def test_seeded_results_are_reproducible():
    cfg1 = make_config(strategy="full", seed=42)
    cfg2 = make_config(strategy="full", seed=42)
    results1 = [cfg1.apply(1.0) for _ in range(5)]
    results2 = [cfg2.apply(1.0) for _ in range(5)]
    assert results1 == results2


def test_describe_disabled():
    cfg = make_config(strategy="none")
    assert "disabled" in cfg.describe()


def test_describe_enabled():
    cfg = make_config(strategy="equal", max_ms=750)
    desc = cfg.describe()
    assert "equal" in desc
    assert "750" in desc


def test_enabled_flag():
    for strategy in ("full", "equal", "decorrelated"):
        cfg = make_config(strategy=strategy)
        assert cfg.enabled()
