import json
import pytest
from cronwrap.tags import (
    TaggedRun,
    save_tagged_run,
    load_tagged_runs,
    filter_by_tag,
    parse_tags,
)


@pytest.fixture
def tags_file(tmp_path):
    return str(tmp_path / "tags.json")


def make_run(run_id="abc", command="echo hi", tags=None, exit_code=0):
    return TaggedRun(run_id=run_id, command=command, tags=tags or [], exit_code=exit_code)


def test_has_tag():
    r = make_run(tags=["prod", "daily"])
    assert r.has_tag("prod")
    assert not r.has_tag("staging")


def test_as_dict():
    r = make_run(run_id="x1", tags=["a"])
    d = r.as_dict()
    assert d["run_id"] == "x1"
    assert d["tags"] == ["a"]


def test_save_and_load(tags_file):
    r = make_run(run_id="r1", tags=["prod"])
    save_tagged_run(r, path=tags_file)
    runs = load_tagged_runs(path=tags_file)
    assert len(runs) == 1
    assert runs[0].run_id == "r1"
    assert runs[0].has_tag("prod")


def test_multiple_saves(tags_file):
    save_tagged_run(make_run(run_id="r1", tags=["a"]), path=tags_file)
    save_tagged_run(make_run(run_id="r2", tags=["b"]), path=tags_file)
    runs = load_tagged_runs(path=tags_file)
    assert len(runs) == 2


def test_load_missing_file(tags_file):
    runs = load_tagged_runs(path=tags_file)
    assert runs == []


def test_filter_by_tag(tags_file):
    save_tagged_run(make_run(run_id="r1", tags=["prod"]), path=tags_file)
    save_tagged_run(make_run(run_id="r2", tags=["staging"]), path=tags_file)
    results = filter_by_tag("prod", path=tags_file)
    assert len(results) == 1
    assert results[0].run_id == "r1"


def test_parse_tags_basic():
    assert parse_tags("prod,daily,backup") == ["prod", "daily", "backup"]


def test_parse_tags_spaces():
    assert parse_tags(" prod , daily ") == ["prod", "daily"]


def test_parse_tags_empty():
    assert parse_tags("") == []
    assert parse_tags(None) == []
