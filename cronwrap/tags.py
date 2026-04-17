"""Tag support for labeling and filtering cron runs."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import json
import os

TAGS_FILE_ENV = "CRONWRAP_TAGS_FILE"
DEFAULT_TAGS_FILE = "/tmp/cronwrap_tags.json"


@dataclass
class TaggedRun:
    run_id: str
    command: str
    tags: List[str] = field(default_factory=list)
    exit_code: Optional[int] = None

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "command": self.command,
            "tags": self.tags,
            "exit_code": self.exit_code,
        }


def _tags_path() -> str:
    return os.environ.get(TAGS_FILE_ENV, DEFAULT_TAGS_FILE)


def save_tagged_run(run: TaggedRun, path: Optional[str] = None) -> None:
    fpath = path or _tags_path()
    entries = _load_all(fpath)
    entries.append(run.as_dict())
    with open(fpath, "w") as f:
        json.dump(entries, f)


def _load_all(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def load_tagged_runs(path: Optional[str] = None) -> List[TaggedRun]:
    fpath = path or _tags_path()
    return [
        TaggedRun(
            run_id=e["run_id"],
            command=e["command"],
            tags=e.get("tags", []),
            exit_code=e.get("exit_code"),
        )
        for e in _load_all(fpath)
    ]


def filter_by_tag(tag: str, path: Optional[str] = None) -> List[TaggedRun]:
    return [r for r in load_tagged_runs(path) if r.has_tag(tag)]


def parse_tags(raw: Optional[str]) -> List[str]:
    """Parse comma-separated tag string into a list."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]
