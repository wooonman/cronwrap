"""Integration-style tests combining RetryPolicy with middleware."""
import pytest
from cronwrap.retry import RetryPolicy, run_with_retry
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_retry import attach_retry_middleware, RetryMiddleware


class FakeContext:
    def __init__(self):
        self.retry_policy = None
        self.retry_state = None
        self.extra = {}


class FakeResult:
    def __init__(self, exit_code=0, timed_out=False):
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.retry_state = None


def simulate_run(policy: RetryPolicy, outcomes: list[tuple[int, bool]]) -> tuple:
    """Simulate a full pre -> retry-loop -> post cycle."""
    chain = MiddlewareChain()
    attach_retry_middleware(chain, policy)

    ctx = FakeContext()
    chain.run_pre(ctx)

    idx = [0]

    def fn():
        r = outcomes[min(idx[0], len(outcomes) - 1)]
        idx[0] += 1
        return r

    state = run_with_retry(policy, fn, sleep_fn=lambda _: None)
    result = FakeResult(exit_code=state.last_exit_code)
    result.retry_state = state
    chain.run_post(ctx, result)
    return ctx, result, state


def test_integration_success_no_retry():
    policy = RetryPolicy(max_attempts=3)
    ctx, result, state = simulate_run(policy, [(0, False)])
    assert state.total_attempts == 1
    assert state.gave_up is False
    assert ctx.extra["retry_attempts"] == 1
    assert ctx.extra["retry_gave_up"] is False


def test_integration_all_fail():
    policy = RetryPolicy(max_attempts=3)
    ctx, result, state = simulate_run(policy, [(1, False)] * 3)
    assert state.total_attempts == 3
    assert state.gave_up is True
    assert ctx.extra["retry_gave_up"] is True


def test_integration_succeed_on_third():
    policy = RetryPolicy(max_attempts=5)
    outcomes = [(1, False), (1, False), (0, False)]
    ctx, result, state = simulate_run(policy, outcomes)
    assert state.total_attempts == 3
    assert state.gave_up is False


def test_integration_specific_exit_code_filter():
    policy = RetryPolicy(max_attempts=3, retry_on_exit_codes=[2])
    # exit code 1 is NOT in the retry list — should stop immediately
    ctx, result, state = simulate_run(policy, [(1, False)])
    assert state.total_attempts == 1
    assert state.gave_up is False
