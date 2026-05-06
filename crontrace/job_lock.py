"""Lightweight advisory locking to prevent overlapping cron job runs."""

import sqlite3
import time
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_locks (
            job_name  TEXT PRIMARY KEY,
            pid       INTEGER NOT NULL,
            acquired  TEXT NOT NULL
        )
        """
    )
    conn.commit()


def acquire_lock(conn: sqlite3.Connection, job_name: str, pid: int, now_utc: str) -> bool:
    """Try to insert a lock row. Returns True if the lock was acquired."""
    _ensure_table(conn)
    try:
        conn.execute(
            "INSERT INTO job_locks (job_name, pid, acquired) VALUES (?, ?, ?)",
            (job_name, pid, now_utc),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def release_lock(conn: sqlite3.Connection, job_name: str) -> None:
    """Remove the lock row for *job_name*."""
    _ensure_table(conn)
    conn.execute("DELETE FROM job_locks WHERE job_name = ?", (job_name,))
    conn.commit()


def get_lock_info(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the current lock info for *job_name*, or None if not locked."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, pid, acquired FROM job_locks WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "pid": row[1], "acquired": row[2]}


def is_locked(conn: sqlite3.Connection, job_name: str) -> bool:
    """Return True if a lock row exists for *job_name*."""
    return get_lock_info(conn, job_name) is not None
