"""Tests for cronwrap.budget and cronwrap.middleware_budget."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from cronwrap.budget import (
    BudgetConfig,
    check_budget,
    remaining_budget,
    reset_budget,
    _prune,
)
from cronwrap.middleware_budget import BudgetMiddleware


@pytest.fixture()
def tmp_cfg(tmp_path: Path) -> BudgetConfig:
    return BudgetConfig(
        enabled=True,
        max_seconds=10.0,
        window_seconds=3600.0,
        job_name="testjob",
        state_dir=str(tmp_path),
    )


def test_disabled_always_allows(tmp_path: Path) -> None:
    cfg = BudgetConfig(enabled=False, max_seconds=1.0, state_dir=str(tmp_path))
    assert check_budget(cfg, 999.0) is True


def test_first_run_within_budget(tmp_cfg: BudgetConfig) -> None:
    assert check_budget(tmp_cfg, 5.0) is True


def test_exceeds_budget(tmp_cfg: BudgetConfig) -> None:
    check_budget(tmp_cfg, 6.0)
    result = check_budget(tmp_cfg, 5.0)  # total = 11 > 10
    assert result is False


def test_exactly_at_budget(tmp_cfg: BudgetConfig) -> None:
    assert check_budget(tmp_cfg, 10.0) is True


def test_remaining_budget_decreases(tmp_cfg: BudgetConfig) -> None:
    rem_before = remaining_budget(tmp_cfg)
    check_budget(tmp_cfg, 3.0)
    rem_after = remaining_budget(tmp_cfg)
    assert rem_before == pytest.approx(10.0)
    assert rem_after == pytest.approx(7.0)


def test_remaining_budget_disabled_returns_none(tmp_path: Path) -> None:
    cfg = BudgetConfig(enabled=False, state_dir=str(tmp_path))
    assert remaining_budget(cfg) is None


def test_reset_clears_state(tmp_cfg: BudgetConfig) -> None:
    check_budget(tmp_cfg, 8.0)
    reset_budget(tmp_cfg)
    assert remaining_budget(tmp_cfg) == pytest.approx(10.0)


def test_prune_removes_old_entries() -> None:
    now = time.time()
    runs = [now - 7200, now - 1800, now - 60]
    pruned = _prune(runs, 3600.0, now)
    assert len(pruned) == 2


def test_middleware_pre_sets_remaining() -> None:
    cfg = BudgetConfig(enabled=False)
    mw = BudgetMiddleware(cfg)
    ctx = MagicMock()
    mw.pre(ctx)
    assert ctx.budget_remaining is None


def test_middleware_post_sets_exceeded_false_when_within(tmp_cfg: BudgetConfig) -> None:
    mw = BudgetMiddleware(tmp_cfg)
    ctx = MagicMock()
    result = MagicMock()
    mw.pre(ctx)
    mw.post(ctx, result)
    assert ctx.budget_exceeded is False


def test_middleware_post_sets_exceeded_true_when_over(tmp_cfg: BudgetConfig) -> None:
    # Pre-fill the budget
    check_budget(tmp_cfg, 9.5)
    mw = BudgetMiddleware(tmp_cfg)
    ctx = MagicMock()
    result = MagicMock()
    mw._start = time.monotonic() - 1.0  # simulate 1s run
    mw.post(ctx, result)
    assert ctx.budget_exceeded is True
