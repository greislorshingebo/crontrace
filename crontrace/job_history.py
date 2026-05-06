"""Provides per-job execution history analysis utilities."""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from crontrace.storage import fetch_recent


def fetch_job_history(conn, job_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Return recent executions for a specific job as a list of dicts."""
    rows = fetch_recent(conn, limit=limit)
    return [
        {
            "id": r[0],
            "job_name": r[1],
            "started_at": r[2],
            "duration": r[3],
            "exit_code": r[4],
            "stdout": r[5] if len(r) > 5 else "",
        }
        for r in rows
        if r[1] == job_name
    ]


def last_success(history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the most recent successful execution or None."""
    for entry in history:
        if entry["exit_code"] == 0:
            return entry
    return None


def last_failure(history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the most recent failed execution or None."""
    for entry in history:
        if entry["exit_code"] != 0:
            return entry
    return None


def streak(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return current streak info: type ('ok'|'fail'|'none'), length."""
    if not history:
        return {"type": "none", "length": 0}

    first_code = history[0]["exit_code"]
    streak_type = "ok" if first_code == 0 else "fail"
    count = 0
    for entry in history:
        if (entry["exit_code"] == 0) == (streak_type == "ok"):
            count += 1
        else:
            break
    return {"type": streak_type, "length": count}


def render_job_history(job_name: str, history: List[Dict[str, Any]]) -> str:
    """Render a plain-text summary of a job's execution history."""
    if not history:
        return f"No history found for job: {job_name}\n"

    lines = [f"History for: {job_name}", "-" * 40]
    for entry in history:
        status = "OK  " if entry["exit_code"] == 0 else "FAIL"
        lines.append(
            f"  [{status}] {entry['started_at']}  exit={entry['exit_code']}  "
            f"duration={entry['duration']:.2f}s"
        )

    s = streak(history)
    lines.append("-" * 40)
    lines.append(f"Current streak: {s['length']} x {s['type'].upper()}")

    ls = last_success(history)
    if ls:
        lines.append(f"Last success:   {ls['started_at']}")

    lf = last_failure(history)
    if lf:
        lines.append(f"Last failure:   {lf['started_at']}")

    return "\n".join(lines) + "\n"
