"""Per-job cooldown enforcement: prevent re-runs within a minimum interval."""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_cooldown (
            job_name  TEXT PRIMARY KEY,
            seconds   INTEGER NOT NULL,
            note      TEXT
        )
        """
    )
    conn.commit()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_cooldown(
    conn: sqlite3.Connection,
    job_name: str,
    seconds: int,
    note: Optional[str] = None,
) -> None:
    """Set (or replace) a cooldown for *job_name*."""
    if seconds < 0:
        raise ValueError("cooldown seconds must be >= 0")
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_cooldown (job_name, seconds, note)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET seconds=excluded.seconds, note=excluded.note
        """,
        (job_name.strip(), seconds, note),
    )
    conn.commit()


def get_cooldown(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the cooldown record for *job_name*, or None."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, seconds, note FROM job_cooldown WHERE job_name = ?",
        (job_name.strip(),),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "seconds": row[1], "note": row[2]}


def delete_cooldown(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove cooldown for *job_name*. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_cooldown WHERE job_name = ?", (job_name.strip(),)
    )
    conn.commit()
    return cur.rowcount > 0


def list_cooldowns(conn: sqlite3.Connection) -> list:
    """Return all cooldown records ordered by job_name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, seconds, note FROM job_cooldown ORDER BY job_name"
    ).fetchall()
    return [{"job_name": r[0], "seconds": r[1], "note": r[2]} for r in rows]


def is_in_cooldown(
    conn: sqlite3.Connection,
    job_name: str,
    last_run_at: Optional[datetime],
) -> bool:
    """Return True when *job_name* has a cooldown and *last_run_at* is recent enough
    that another run should be suppressed."""
    record = get_cooldown(conn, job_name)
    if record is None:
        return False
    if last_run_at is None:
        return False
    if last_run_at.tzinfo is None:
        last_run_at = last_run_at.replace(tzinfo=timezone.utc)
    elapsed = (_utcnow() - last_run_at).total_seconds()
    return elapsed < record["seconds"]
