"""Threshold-based alerting: flag jobs whose failure rate or avg duration
exceeds configurable limits."""

from __future__ import annotations

from typing import Sequence

# Each row is a sqlite3.Row / dict-like: (id, job_name, started_at, duration_s, exit_code, stdout, stderr)

DEFAULT_FAILURE_RATE_THRESHOLD = 0.5   # 50 %
DEFAULT_DURATION_THRESHOLD_S   = 300.0  # 5 minutes


def _failure_rate(rows: Sequence) -> float:
    """Return fraction of rows with non-zero exit_code."""
    if not rows:
        return 0.0
    failures = sum(1 for r in rows if r["exit_code"] != 0)
    return failures / len(rows)


def _avg_duration(rows: Sequence) -> float:
    """Return average duration_s across rows, or 0.0 for empty input."""
    if not rows:
        return 0.0
    return sum(r["duration_s"] for r in rows) / len(rows)


def check_failure_rate(
    rows: Sequence,
    threshold: float = DEFAULT_FAILURE_RATE_THRESHOLD,
) -> dict:
    """Return an alert dict if failure rate exceeds *threshold*, else None."""
    rate = _failure_rate(rows)
    if rate > threshold:
        return {
            "type": "failure_rate",
            "value": round(rate, 4),
            "threshold": threshold,
            "message": f"Failure rate {rate:.1%} exceeds threshold {threshold:.1%}",
        }
    return None


def check_avg_duration(
    rows: Sequence,
    threshold: float = DEFAULT_DURATION_THRESHOLD_S,
) -> dict:
    """Return an alert dict if average duration exceeds *threshold*, else None."""
    avg = _avg_duration(rows)
    if avg > threshold:
        return {
            "type": "avg_duration",
            "value": round(avg, 2),
            "threshold": threshold,
            "message": f"Average duration {avg:.1f}s exceeds threshold {threshold:.1f}s",
        }
    return None


def check_consecutive_failures(rows: Sequence, limit: int = 3) -> dict | None:
    """Return an alert dict if the most recent *limit* runs all failed.

    Rows are assumed to be ordered oldest-first (as returned by a
    ``SELECT … ORDER BY started_at ASC`` query).  Only the tail of the
    sequence is examined, so a single recent success clears the alert.
    """
    if len(rows) < limit:
        return None
    recent = rows[-limit:]
    if all(r["exit_code"] != 0 for r in recent):
        return {
            "type": "consecutive_failures",
            "value": limit,
            "threshold": limit,
            "message": f"Last {limit} consecutive runs all failed",
        }
    return None


def evaluate_alerts(
    rows: Sequence,
    failure_rate_threshold: float = DEFAULT_FAILURE_RATE_THRESHOLD,
    duration_threshold_s: float = DEFAULT_DURATION_THRESHOLD_S,
    consecutive_failures_limit: int = 3,
) -> list[dict]:
    """Run all checks and return a (possibly empty) list of alert dicts."""
    alerts = []
    fr = check_failure_rate(rows, failure_rate_threshold)
    if fr:
        alerts.append(fr)
    dur = check_avg_duration(rows, duration_threshold_s)
    if dur:
        alerts.append(dur)
    cf = check_consecutive_failures(rows, consecutive_failures_limit)
    if cf:
        alerts.append(cf)
    return alerts
