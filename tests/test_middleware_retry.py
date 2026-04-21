"""Tests for cronwrap.middleware_retry."""
import pytest
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_retry import RetryMiddleware, attach_retry_middleware
from cronwrap.retry import RetryPolicy, RetryState


class FakeContext:
    def __init__(self):
        self.retry_policy = None
        self.retry_state = None
        self.extra = {}


class FakeResult:
    def __init__(self, retry_state=None):
        self.retry_state = retry_state


def test_pre_sets_policy_on_context():
    policy = RetryPolicy(max_attempts=3)
    mw = RetryMiddleware(policy)
    ctx = FakeContext()
    mw.pre(ctx)
    assert ctx.retry_policy is policy
    assert ctx.retry_state is None


def test_post_sets_state_on_context():
    policy = RetryPolicy(max_attempts=3)
    mw = RetryMiddleware(policy)
    ctx = FakeContext()
    mw.pre(ctx)

    state = RetryState(attempt=2, total_attempts=3, gave_up=True, last_exit_code=1)
    result = FakeResult(retry_state=state)
    mw.post(ctx, result)

    assert ctx.retry_state is state
    assert ctx.extra["retry_attempts"] == 3
    assert ctx.extra["retry_gave_up"] is True


def test_post_no_state_on_result():
    policy = RetryPolicy(max_attempts=1)
    mw = RetryMiddleware(policy)
    ctx = FakeContext()
    mw.pre(ctx)
    result = FakeResult(retry_state=None)
    mw.post(ctx, result)
    assert ctx.retry_state is None


def test_attach_adds_hooks_to_chain():
    chain = MiddlewareChain()
    policy = RetryPolicy(max_attempts=2)
    mw = attach_retry_middleware(chain, policy)
    assert isinstance(mw, RetryMiddleware)
    assert len(chain._pre) == 1
    assert len(chain._post) == 1


def test_attach_and_run_pre_post():
    chain = MiddlewareChain()
    policy = RetryPolicy(max_attempts=2)
    attach_retry_middleware(chain, policy)

    ctx = FakeContext()
    chain.run_pre(ctx)
    assert ctx.retry_policy.max_attempts == 2

    state = RetryState(attempt=1, total_attempts=2, gave_up=True, last_exit_code=1)
    result = FakeResult(retry_state=state)
    chain.run_post(ctx, result)
    assert ctx.extra["retry_attempts"] == 2
