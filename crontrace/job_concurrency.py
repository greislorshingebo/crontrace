"""Track and enforce concurrency limits for cron jobs."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_concurrency (
            job_name  TEXT PRIMARY KEY,
            max_concurrent INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_concurrency(conn: sqlite3.Connection, job_name: str, max_concurrent: int) -> None:
    """Set the maximum allowed concurrent runs for a job."""
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1")
    _ensure_table(conn)
    from crontrace.runner import _now_utc
    conn.execute(
        """
        INSERT INTO job_concurrency (job_name, max_concurrent, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            max_concurrent = excluded.max_concurrent,
            updated_at     = excluded.updated_at
        """,
        (job_name, max_concurrent, _now_utc()),
    )
    conn.commit()


def get_concurrency(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return concurrency config for a job, or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, max_concurrent, updated_at FROM job_concurrency WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "max_concurrent": row[1], "updated_at": row[2]}


def delete_concurrency(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove concurrency config for a job. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_concurrency WHERE job_name = ?", (job_name,)
    )
    conn.commit()
    return cur.rowcount > 0


def list_concurrency(conn: sqlite3.Connection) -> list:
    """Return all concurrency configs ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, max_concurrent, updated_at FROM job_concurrency ORDER BY job_name"
    ).fetchall()
    return [{"job_name": r[0], "max_concurrent": r[1], "updated_at": r[2]} for r in rows]


def would_exceed(conn: sqlite3.Connection, job_name: str, active_count: int) -> bool:
    """Return True if starting another run would exceed the concurrency limit."""
    cfg = get_concurrency(conn, job_name)
    if cfg is None:
        return False  # no limit configured
    return active_count >= cfg["max_concurrent"]
