"""Simple metrics collection for cron job runs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class RunMetric:
    job_name: str
    started_at: str
    duration_seconds: float
    exit_code: int
    retries: int = 0
    timed_out: bool = False
    tags: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def _metrics_path(base_dir: str, job_name: str) -> Path:
    safe = job_name.replace(" ", "_").replace("/", "-")
    return Path(base_dir) / f"{safe}.metrics.jsonl"


def record_metric(metric: RunMetric, base_dir: str = "/tmp/cronwrap/metrics") -> None:
    os.makedirs(base_dir, exist_ok=True)
    path = _metrics_path(base_dir, metric.job_name)
    with open(path, "a") as f:
        f.write(json.dumps(asdict(metric)) + "\n")


def read_metrics(job_name: str, base_dir: str = "/tmp/cronwrap/metrics", limit: int = 100) -> List[RunMetric]:
    path = _metrics_path(base_dir, job_name)
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    entries = [RunMetric(**json.loads(l)) for l in lines]
    return entries[-limit:]


def aggregate(metrics: List[RunMetric]) -> dict:
    if not metrics:
        return {"count": 0}
    durations = [m.duration_seconds for m in metrics]
    successes = [m for m in metrics if m.success]
    return {
        "count": len(metrics),
        "success_count": len(successes),
        "failure_count": len(metrics) - len(successes),
        "success_rate": round(len(successes) / len(metrics) * 100, 1),
        "avg_duration": round(sum(durations) / len(durations), 3),
        "max_duration": round(max(durations), 3),
        "min_duration": round(min(durations), 3),
        "total_retries": sum(m.retries for m in metrics),
    }
