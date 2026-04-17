import pytest
from cronwrap.middleware import MiddlewareChain
from cronwrap.middleware_tags import TagsMiddleware, attach_tags_middleware
from cronwrap.tags import load_tagged_runs


class FakeResult:
    def __init__(self, exit_code=0):
        self.exit_code = exit_code


@pytest.fixture
def tags_file(tmp_path):
    return str(tmp_path / "tags.json")


def test_tags_middleware_saves_run(tags_file):
    mw = TagsMiddleware(tags=["prod"], tags_file=tags_file)
    mw.pre({"run_id": "abc", "command": "echo hi"})
    mw.post({}, FakeResult(exit_code=0))

    runs = load_tagged_runs(path=tags_file)
    assert len(runs) == 1
    assert runs[0].run_id == "abc"
    assert runs[0].has_tag("prod")
    assert runs[0].exit_code == 0


def test_tags_middleware_failure(tags_file):
    mw = TagsMiddleware(tags=["nightly"], tags_file=tags_file)
    mw.pre({"run_id": "xyz", "command": "false"})
    mw.post({}, FakeResult(exit_code=1))

    runs = load_tagged_runs(path=tags_file)
    assert runs[0].exit_code == 1


def test_attach_tags_middleware_from_raw(tags_file):
    chain = MiddlewareChain()
    attach_tags_middleware(chain, tags_raw="prod,daily", tags_file=tags_file)

    context = {"run_id": "r1", "command": "ls"}
    chain.run_pre(context)
    chain.run_post(context, FakeResult())

    runs = load_tagged_runs(path=tags_file)
    assert "prod" in runs[0].tags
    assert "daily" in runs[0].tags


def test_attach_tags_middleware_from_list(tags_file):
    chain = MiddlewareChain()
    attach_tags_middleware(chain, tags=["staging"], tags_file=tags_file)

    chain.run_pre({"run_id": "r2", "command": "pwd"})
    chain.run_post({}, FakeResult())

    runs = load_tagged_runs(path=tags_file)
    assert runs[0].has_tag("staging")


def test_no_tags_saves_empty(tags_file):
    chain = MiddlewareChain()
    attach_tags_middleware(chain, tags=[], tags_file=tags_file)
    chain.run_pre({"run_id": "r3", "command": "date"})
    chain.run_post({}, FakeResult())

    runs = load_tagged_runs(path=tags_file)
    assert runs[0].tags == []
