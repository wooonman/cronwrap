"""Text-based dashboard for displaying metrics summaries."""
from __future__ import annotations

from typing import List
from cronwrap.metrics import read_metrics, aggregate, RunMetric


def _bar(value: float, total: float, width: int = 20) -> str:
    filled = int(round(value / total * width)) if total else 0
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def print_dashboard(job_name: str, base_dir: str = "/tmp/cronwrap/metrics", limit: int = 50) -> None:
    metrics = read_metrics(job_name, base_dir=base_dir, limit=limit)
    if not metrics:
        print(f"No metrics found for job: {job_name}")
        return

    agg = aggregate(metrics)
    print(f"\n{'='*40}")
    print(f"  Job: {job_name}")
    print(f"{'='*40}")
    print(f"  Runs (last {limit}): {agg['count']}")
    print(f"  Success: {agg['success_count']}  Failure: {agg['failure_count']}")
    bar = _bar(agg['success_count'], agg['count'])
    print(f"  Success rate: {agg['success_rate']}% {bar}")
    print(f"  Avg duration : {agg['avg_duration']}s")
    print(f"  Min duration : {agg['min_duration']}s")
    print(f"  Max duration : {agg['max_duration']}s")
    print(f"  Total retries: {agg['total_retries']}")
    print()
    print("  Recent runs:")
    for m in metrics[-5:]:
        status = "OK" if m.success else "FAIL"
        timeout = " [TIMEOUT]" if m.timed_out else ""
        print(f"    {m.started_at[:19]}  {status:4s}  {m.duration_seconds:.2f}s  retries={m.retries}{timeout}")
    print(f"{'='*40}\n")
