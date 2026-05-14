"""Per-job run quota enforcement: limit how many times a job may run per time window."""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

_VALID_WINDOWS = {"hour", "day", "week"}


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_quotas (
            job_name  TEXT PRIMARY KEY,
            max_runs  INTEGER NOT NULL,
            window    TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_quota(
    conn: sqlite3.Connection, job_name: str, max_runs: int, window: str
) -> None:
    """Set or replace the quota for *job_name*."""
    if window not in _VALID_WINDOWS:
        raise ValueError(f"window must be one of {_VALID_WINDOWS}, got {window!r}")
    if max_runs < 1:
        raise ValueError("max_runs must be >= 1")
    _ensure_table(conn)
    conn.execute(
        "INSERT OR REPLACE INTO job_quotas (job_name, max_runs, window) VALUES (?, ?, ?)",
        (job_name, max_runs, window),
    )
    conn.commit()


def get_quota(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the quota dict for *job_name*, or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT max_runs, window FROM job_quotas WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": job_name, "max_runs": row[0], "window": row[1]}


def delete_quota(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the quota for *job_name*. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_quotas WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0


def list_quotas(conn: sqlite3.Connection) -> list:
    """Return all configured quotas as a list of dicts."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, max_runs, window FROM job_quotas ORDER BY job_name"
    ).fetchall()
    return [{"job_name": r[0], "max_runs": r[1], "window": r[2]} for r in rows]


def _window_start(window: str, now: Optional[datetime] = None) -> str:
    """Return an ISO-8601 UTC timestamp for the start of the current window."""
    now = now or _utcnow()
    if window == "hour":
        start = now.replace(minute=0, second=0, microsecond=0)
    elif window == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:  # week
        start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    return start.strftime("%Y-%m-%dT%H:%M:%SZ")


def is_quota_exceeded(conn: sqlite3.Connection, job_name: str) -> bool:
    """Return True if *job_name* has reached its run quota for the current window.

    Uses the *executions* table written by runner.run_job.  Returns False when
    no quota is configured or the executions table does not exist.
    """
    quota = get_quota(conn, job_name)
    if quota is None:
        return False
    start_ts = _window_start(quota["window"])
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM executions WHERE job_name = ? AND started_at >= ?",
            (job_name, start_ts),
        ).fetchone()
    except sqlite3.OperationalError:
        return False
    return row[0] >= quota["max_runs"]
