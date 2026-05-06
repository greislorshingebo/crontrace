"""Deduplicator: suppress duplicate notifications for repeated failures.

Tracks the last-notified exit code per job so that a webhook/stdout
notification is only dispatched when the outcome *changes* (e.g. a job
that keeps failing does not spam the notification channel).
"""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dedup_state (
            job_name  TEXT PRIMARY KEY,
            last_code INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def get_last_code(conn: sqlite3.Connection, job_name: str) -> Optional[int]:
    """Return the exit code recorded during the previous notification, or None."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT last_code FROM dedup_state WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    return int(row[0]) if row is not None else None


def set_last_code(
    conn: sqlite3.Connection, job_name: str, exit_code: int, updated_at: str
) -> None:
    """Upsert the last-notified exit code for *job_name*."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO dedup_state (job_name, last_code, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            last_code  = excluded.last_code,
            updated_at = excluded.updated_at
        """,
        (job_name, exit_code, updated_at),
    )
    conn.commit()


def should_notify(
    conn: sqlite3.Connection, job_name: str, exit_code: int
) -> bool:
    """Return True when the exit code differs from the previously recorded one.

    A job that has never been seen before always returns True.
    """
    last = get_last_code(conn, job_name)
    return last is None or last != exit_code
