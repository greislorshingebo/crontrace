"""Per-job timeout configuration and enforcement helpers."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_timeouts (
            job_name  TEXT PRIMARY KEY,
            timeout_s INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_timeout(conn: sqlite3.Connection, job_name: str, timeout_s: int) -> None:
    """Store or overwrite the timeout (seconds) for *job_name*."""
    if timeout_s <= 0:
        raise ValueError("timeout_s must be a positive integer")
    _ensure_table(conn)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        """
        INSERT INTO job_timeouts (job_name, timeout_s, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            timeout_s  = excluded.timeout_s,
            updated_at = excluded.updated_at
        """,
        (job_name, timeout_s, now),
    )
    conn.commit()


def get_timeout(conn: sqlite3.Connection, job_name: str) -> Optional[int]:
    """Return the configured timeout in seconds, or *None* if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT timeout_s FROM job_timeouts WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    return row[0] if row else None


def delete_timeout(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the timeout entry for *job_name*. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_timeouts WHERE job_name = ?", (job_name,)
    )
    conn.commit()
    return cur.rowcount > 0


def list_timeouts(conn: sqlite3.Connection) -> list[dict]:
    """Return all configured timeouts as a list of dicts."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, timeout_s, updated_at FROM job_timeouts ORDER BY job_name"
    ).fetchall()
    return [{"job_name": r[0], "timeout_s": r[1], "updated_at": r[2]} for r in rows]


def is_timed_out(duration_s: float, job_name: str, conn: sqlite3.Connection) -> bool:
    """Return True when *duration_s* exceeds the configured timeout for *job_name*."""
    limit = get_timeout(conn, job_name)
    if limit is None:
        return False
    return duration_s > limit
