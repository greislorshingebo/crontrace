"""Per-job retry configuration and tracking."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_retries (
            job_name  TEXT PRIMARY KEY,
            max_retries INTEGER NOT NULL DEFAULT 3,
            retry_delay INTEGER NOT NULL DEFAULT 60,
            note      TEXT
        )
        """
    )
    conn.commit()


def set_retry_policy(
    conn: sqlite3.Connection,
    job_name: str,
    max_retries: int,
    retry_delay: int = 60,
    note: Optional[str] = None,
) -> None:
    """Insert or replace the retry policy for a job."""
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if retry_delay < 0:
        raise ValueError("retry_delay must be >= 0")
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_retries (job_name, max_retries, retry_delay, note)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            max_retries  = excluded.max_retries,
            retry_delay  = excluded.retry_delay,
            note         = excluded.note
        """,
        (job_name.strip(), max_retries, retry_delay, note),
    )
    conn.commit()


def get_retry_policy(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the retry policy dict for a job, or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, max_retries, retry_delay, note FROM job_retries WHERE job_name = ?",
        (job_name.strip(),),
    ).fetchone()
    if row is None:
        return None
    return {
        "job_name": row[0],
        "max_retries": row[1],
        "retry_delay": row[2],
        "note": row[3],
    }


def delete_retry_policy(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the retry policy for a job. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_retries WHERE job_name = ?", (job_name.strip(),)
    )
    conn.commit()
    return cur.rowcount > 0


def list_retry_policies(conn: sqlite3.Connection) -> list:
    """Return all retry policies ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, max_retries, retry_delay, note FROM job_retries ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "max_retries": r[1], "retry_delay": r[2], "note": r[3]}
        for r in rows
    ]
