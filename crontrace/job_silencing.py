"""Manage silenced (suppressed) jobs — silenced jobs skip notifications."""

import sqlite3
from typing import Optional

_VALID_REASONS = {"maintenance", "flapping", "expected", "other"}


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_silencing (
            job_name  TEXT PRIMARY KEY,
            reason    TEXT NOT NULL DEFAULT 'other',
            note      TEXT,
            silenced_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def silence_job(
    conn: sqlite3.Connection,
    job_name: str,
    reason: str = "other",
    note: Optional[str] = None,
    silenced_at: Optional[str] = None,
) -> None:
    """Mark a job as silenced.  Overwrites any existing entry."""
    if reason not in _VALID_REASONS:
        raise ValueError(f"Invalid reason {reason!r}. Choose from {_VALID_REASONS}.")
    job_name = job_name.strip()
    if not job_name:
        raise ValueError("job_name must not be empty")
    from crontrace.runner import _now_utc  # local import to avoid circular deps
    ts = silenced_at or _now_utc()
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_silencing (job_name, reason, note, silenced_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            reason     = excluded.reason,
            note       = excluded.note,
            silenced_at = excluded.silenced_at
        """,
        (job_name, reason, note, ts),
    )
    conn.commit()


def unsilence_job(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove silencing for a job.  Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_silencing WHERE job_name = ?", (job_name.strip(),)
    )
    conn.commit()
    return cur.rowcount > 0


def get_silencing(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the silencing record for a job, or None if not silenced."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, reason, note, silenced_at FROM job_silencing WHERE job_name = ?",
        (job_name.strip(),),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "reason": row[1], "note": row[2], "silenced_at": row[3]}


def list_silenced(conn: sqlite3.Connection) -> list:
    """Return all silenced jobs ordered by job_name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, reason, note, silenced_at FROM job_silencing ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "reason": r[1], "note": r[2], "silenced_at": r[3]}
        for r in rows
    ]


def is_silenced(conn: sqlite3.Connection, job_name: str) -> bool:
    """Return True if the job currently has an active silencing entry."""
    return get_silencing(conn, job_name) is not None
