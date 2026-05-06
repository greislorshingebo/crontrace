"""Aggregate per-job metrics: success rate, duration percentiles, run count."""

from __future__ import annotations

import statistics
from typing import Any


def _exit_codes(rows: list[tuple]) -> list[int]:
    """Extract exit codes from storage rows (index 3)."""
    return [r[3] for r in rows]


def _durations(rows: list[tuple]) -> list[float]:
    """Extract durations from storage rows (index 4)."""
    return [r[4] for r in rows]


def success_rate(rows: list[tuple]) -> float:
    """Return fraction of rows with exit_code == 0. Returns 0.0 for empty."""
    if not rows:
        return 0.0
    codes = _exit_codes(rows)
    return sum(1 for c in codes if c == 0) / len(codes)


def run_count(rows: list[tuple]) -> int:
    """Total number of executions."""
    return len(rows)


def duration_percentile(rows: list[tuple], pct: float) -> float | None:
    """Return the p-th percentile (0-100) of durations, or None if empty."""
    if not rows:
        return None
    durs = sorted(_durations(rows))
    if pct <= 0:
        return durs[0]
    if pct >= 100:
        return durs[-1]
    idx = (pct / 100) * (len(durs) - 1)
    lo, hi = int(idx), min(int(idx) + 1, len(durs) - 1)
    frac = idx - lo
    return durs[lo] + frac * (durs[hi] - durs[lo])


def median_duration(rows: list[tuple]) -> float | None:
    """Median execution duration in seconds, or None if empty."""
    return duration_percentile(rows, 50)


def compute_metrics(job_name: str, rows: list[tuple]) -> dict[str, Any]:
    """Return a metrics dict for *job_name* computed from *rows*."""
    durs = _durations(rows) if rows else []
    return {
        "job": job_name,
        "run_count": run_count(rows),
        "success_rate": round(success_rate(rows), 4),
        "median_duration": round(median_duration(rows), 3) if rows else None,
        "p95_duration": round(duration_percentile(rows, 95), 3) if rows else None,
        "min_duration": round(min(durs), 3) if durs else None,
        "max_duration": round(max(durs), 3) if durs else None,
    }
