"""Tests for cronwrap.retry."""
import pytest
from cronwrap.retry import RetryPolicy, RetryState, run_with_retry


def test_default_policy_not_enabled():
    p = RetryPolicy()
    assert p.enabled is False


def test_enabled_when_max_attempts_gt_1():
    p = RetryPolicy(max_attempts=3)
    assert p.enabled is True


def test_from_dict_full():
    p = RetryPolicy.from_dict(
        {"max_attempts": 4, "delay": 1.5, "backoff": 2.0,
         "retry_on_exit_codes": [1, 2], "retry_on_timeout": True}
    )
    assert p.max_attempts == 4
    assert p.delay == 1.5
    assert p.backoff == 2.0
    assert p.retry_on_exit_codes == [1, 2]
    assert p.retry_on_timeout is True


def test_from_dict_defaults():
    p = RetryPolicy.from_dict({})
    assert p.max_attempts == 1
    assert p.delay == 0.0
    assert p.backoff == 1.0
    assert p.retry_on_exit_codes == []
    assert p.retry_on_timeout is False


def test_should_retry_nonzero_exit_no_filter():
    p = RetryPolicy(max_attempts=3)
    assert p.should_retry(1) is True
    assert p.should_retry(0) is False


def test_should_retry_specific_codes():
    p = RetryPolicy(max_attempts=3, retry_on_exit_codes=[2, 3])
    assert p.should_retry(2) is True
    assert p.should_retry(1) is False


def test_should_retry_timeout():
    p = RetryPolicy(max_attempts=3, retry_on_timeout=True)
    assert p.should_retry(0, timed_out=True) is True
    p2 = RetryPolicy(max_attempts=3, retry_on_timeout=False)
    assert p2.should_retry(0, timed_out=True) is False


def test_delay_for_first_attempt_is_zero():
    p = RetryPolicy(max_attempts=3, delay=2.0, backoff=2.0)
    assert p.delay_for(0) == 0.0


def test_delay_for_backoff():
    p = RetryPolicy(max_attempts=4, delay=1.0, backoff=2.0)
    assert p.delay_for(1) == 1.0
    assert p.delay_for(2) == 2.0
    assert p.delay_for(3) == 4.0


def test_run_with_retry_succeeds_first_try():
    calls = []

    def fn():
        calls.append(1)
        return (0, False)

    p = RetryPolicy(max_attempts=3)
    state = run_with_retry(p, fn, sleep_fn=lambda _: None)
    assert state.total_attempts == 1
    assert state.gave_up is False
    assert state.last_exit_code == 0


def test_run_with_retry_exhausts():
    def fn():
        return (1, False)

    p = RetryPolicy(max_attempts=3)
    state = run_with_retry(p, fn, sleep_fn=lambda _: None)
    assert state.total_attempts == 3
    assert state.gave_up is True


def test_run_with_retry_succeeds_on_second():
    results = [(1, False), (0, False)]
    idx = [0]

    def fn():
        r = results[idx[0]]
        idx[0] += 1
        return r

    p = RetryPolicy(max_attempts=3)
    state = run_with_retry(p, fn, sleep_fn=lambda _: None)
    assert state.total_attempts == 2
    assert state.gave_up is False


def test_run_with_retry_calls_sleep():
    slept = []

    def fn():
        return (1, False)

    p = RetryPolicy(max_attempts=3, delay=1.0, backoff=1.0)
    run_with_retry(p, fn, sleep_fn=lambda s: slept.append(s))
    # first attempt has no sleep, subsequent ones do
    assert len(slept) == 2
    assert all(s == 1.0 for s in slept)
