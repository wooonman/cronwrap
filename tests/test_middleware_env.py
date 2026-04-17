"""Tests for cronwrap.middleware_env."""
import pytest

from cronwrap.env import EnvConfig
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_env import EnvMiddleware, attach_env_middleware


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code
        self.stdout = ""
        self.stderr = ""


def test_env_middleware_sets_env_on_context():
    cfg = EnvConfig(vars={"MY_VAR": "hello"}, inherit=False)
    mw = EnvMiddleware(cfg)
    ctx = {}
    mw.pre(ctx)
    assert ctx["env"]["MY_VAR"] == "hello"


def test_env_middleware_redacts_masked():
    cfg = EnvConfig(vars={"SECRET": "s3cr3t", "SAFE": "ok"}, inherit=False, mask=["SECRET"])
    mw = EnvMiddleware(cfg)
    ctx = {}
    mw.pre(ctx)
    assert ctx["env_redacted"]["SECRET"] == "***"
    assert ctx["env_redacted"]["SAFE"] == "ok"
    # Original env is unredacted
    assert ctx["env"]["SECRET"] == "s3cr3t"


def test_env_middleware_post_is_noop():
    cfg = EnvConfig(inherit=False)
    mw = EnvMiddleware(cfg)
    ctx = {}
    mw.pre(ctx)
    mw.post(ctx, FakeResult())  # should not raise


def test_attach_env_middleware_hooks_chain():
    chain = MiddlewareChain()
    cfg = EnvConfig(vars={"A": "1"}, inherit=False)
    attach_env_middleware(chain, cfg)
    ctx = {}
    chain.run_pre(ctx)
    assert ctx["env"] == {"A": "1"}


def test_attach_env_middleware_default_config():
    chain = MiddlewareChain()
    mw = attach_env_middleware(chain)  # no config -> defaults
    assert mw.config.inherit is True
    ctx = {}
    chain.run_pre(ctx)
    # Should have inherited OS env
    assert len(ctx["env"]) > 0
