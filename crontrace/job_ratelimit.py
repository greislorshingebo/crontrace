"""Per-job rate limiting: cap how many times a job may run within a sliding window."""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_ratelimit (
            job_name  TEXT PRIMARY KEY,
            max_runs  INTEGER NOT NULL,
            window_s  INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def set_ratelimit(conn: sqlite3.Connection, job_name: str, max_runs: int, window_seconds: int) -> None:
    """Set or replace the rate-limit rule for *job_name*."""
    if max_runs < 1:
        raise ValueError("max_runs must be >= 1")
    if window_seconds < 1:
        raise ValueError("window_seconds must be >= 1")
    _ensure_table(conn)
    conn.execute(
        "INSERT INTO job_ratelimit (job_name, max_runs, window_s) VALUES (?, ?, ?)"
        " ON CONFLICT(job_name) DO UPDATE SET max_runs=excluded.max_runs, window_s=excluded.window_s",
        (job_name, max_runs, window_seconds),
    )
    conn.commit()


def get_ratelimit(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the rate-limit rule for *job_name*, or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, max_runs, window_s FROM job_ratelimit WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "max_runs": row[1], "window_s": row[2]}


def delete_ratelimit(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the rate-limit rule for *job_name*. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_ratelimit WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0


def list_ratelimits(conn: sqlite3.Connection) -> list:
    """Return all rate-limit rules ordered by job_name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, max_runs, window_s FROM job_ratelimit ORDER BY job_name"
    ).fetchall()
    return [{"job_name": r[0], "max_runs": r[1], "window_s": r[2]} for r in rows]


def is_rate_limited(conn: sqlite3.Connection, job_name: str) -> bool:
    """Return True if *job_name* has exceeded its allowed runs in the sliding window.

    Requires the *executions* table created by crontrace.storage.
    If no rule is configured the job is never considered rate-limited.
    """
    rule = get_ratelimit(conn, job_name)
    if rule is None:
        return False

    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=rule["window_s"])).isoformat()
    (count,) = conn.execute(
        "SELECT COUNT(*) FROM executions WHERE job_name = ? AND started_at >= ?",
        (job_name, cutoff),
    ).fetchone()
    return count >= rule["max_runs"]
