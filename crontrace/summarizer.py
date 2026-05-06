"""Summarizer: compute aggregate statistics over execution records."""

from __future__ import annotations

from typing import Any


def _safe_avg(values: list[float]) -> float | None:
    """Return the mean of *values*, or None if the list is empty."""
    if not values:
        return None
    return sum(values) / len(values)


def summarize(rows: list[tuple[Any, ...]]) -> dict[str, Any]:
    """Return aggregate statistics for a list of execution rows.

    Each row is expected to be a tuple produced by ``fetch_recent``:
        (id, job_name, started_at, duration_s, exit_code, stdout, stderr)

    Returns a dict with keys:
        total        – total number of runs
        successes    – runs where exit_code == 0
        failures     – runs where exit_code != 0
        success_rate – fraction in [0, 1] (None when total == 0)
        avg_duration – average duration in seconds (None when total == 0)
        min_duration – shortest run in seconds (None when total == 0)
        max_duration – longest run in seconds (None when total == 0)
        last_exit    – exit code of the most recent run (None when total == 0)
    """
    if not rows:
        return {
            "total": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": None,
            "avg_duration": None,
            "min_duration": None,
            "max_duration": None,
            "last_exit": None,
        }

    durations: list[float] = [float(r[3]) for r in rows]
    exit_codes: list[int] = [int(r[4]) for r in rows]

    successes = sum(1 for ec in exit_codes if ec == 0)
    failures = len(exit_codes) - successes

    return {
        "total": len(rows),
        "successes": successes,
        "failures": failures,
        "success_rate": successes / len(rows),
        "avg_duration": _safe_avg(durations),
        "min_duration": min(durations),
        "max_duration": max(durations),
        "last_exit": exit_codes[-1],
    }
