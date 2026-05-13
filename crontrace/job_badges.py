"""Badge generation for job health status."""

import sqlite3
from typing import Optional

BADGE_OK = "passing"
BADGE_FAIL = "failing"
BADGE_WARN = "warning"
BADGE_UNKNOWN = "unknown"

_COLORS = {
    BADGE_OK: "brightgreen",
    BADGE_FAIL: "red",
    BADGE_WARN: "yellow",
    BADGE_UNKNOWN: "lightgrey",
}


def _status_from_rows(rows: list) -> str:
    """Derive badge status from a list of execution row dicts."""
    if not rows:
        return BADGE_UNKNOWN
    recent = rows[:5]
    failures = sum(1 for r in recent if r["exit_code"] != 0)
    if failures == 0:
        return BADGE_OK
    if failures == len(recent):
        return BADGE_FAIL
    return BADGE_WARN


def get_badge_status(conn: sqlite3.Connection, job_name: str) -> str:
    """Return the badge status string for *job_name*."""
    cur = conn.execute(
        "SELECT exit_code FROM executions WHERE job_name = ? ORDER BY started_at DESC LIMIT 5",
        (job_name,),
    )
    rows = [{"exit_code": r[0]} for r in cur.fetchall()]
    return _status_from_rows(rows)


def get_badge_color(status: str) -> str:
    """Return a Shields.io-compatible colour name for *status*."""
    return _COLORS.get(status, _COLORS[BADGE_UNKNOWN])


def render_badge_json(job_name: str, status: str) -> dict:
    """Return a Shields.io endpoint-compatible dict for *job_name*."""
    color = get_badge_color(status)
    return {
        "schemaVersion": 1,
        "label": job_name,
        "message": status,
        "color": color,
    }


def render_badge_text(job_name: str, status: str) -> str:
    """Return a compact text badge line suitable for terminal output."""
    color = get_badge_color(status)
    return f"[{job_name}] {status} ({color})"
