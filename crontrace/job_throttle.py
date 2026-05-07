"""Rate-limiting / throttle guard for cron jobs.

Prevents a job from running more frequently than a configured minimum
interval (in seconds).  State is persisted in the crontrace SQLite
database so it survives process restarts.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_throttle (
            job_name  TEXT PRIMARY KEY,
            last_run  TEXT NOT NULL
        )
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_run(conn: sqlite3.Connection, job_name: str) -> None:
    """Persist the current UTC timestamp as the last run time for *job_name*."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_throttle (job_name, last_run)
        VALUES (?, ?)
        ON CONFLICT(job_name) DO UPDATE SET last_run = excluded.last_run
        """,
        (job_name, _utcnow()),
    )
    conn.commit()


def get_last_run(conn: sqlite3.Connection, job_name: str) -> Optional[str]:
    """Return the ISO-8601 UTC timestamp of the last recorded run, or None."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT last_run FROM job_throttle WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    return row[0] if row else None


def is_throttled(
    conn: sqlite3.Connection,
    job_name: str,
    min_interval_seconds: float,
) -> bool:
    """Return True if *job_name* ran within the last *min_interval_seconds*."""
    last = get_last_run(conn, job_name)
    if last is None:
        return False
    last_dt = datetime.fromisoformat(last)
    now_dt = datetime.now(timezone.utc)
    elapsed = (now_dt - last_dt).total_seconds()
    return elapsed < min_interval_seconds


def clear_throttle(conn: sqlite3.Connection, job_name: str) -> None:
    """Remove the throttle record for *job_name* (useful for testing / resets)."""
    _ensure_table(conn)
    conn.execute("DELETE FROM job_throttle WHERE job_name = ?", (job_name,))
    conn.commit()
