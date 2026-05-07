"""Job catalog: register, describe, and list known cron jobs."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_catalog (
            job_name  TEXT PRIMARY KEY,
            command   TEXT NOT NULL,
            schedule  TEXT,
            description TEXT,
            owner     TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def register_job(
    conn: sqlite3.Connection,
    job_name: str,
    command: str,
    schedule: Optional[str] = None,
    description: Optional[str] = None,
    owner: Optional[str] = None,
) -> None:
    """Insert or replace a job entry in the catalog."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_catalog (job_name, command, schedule, description, owner)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            command     = excluded.command,
            schedule    = excluded.schedule,
            description = excluded.description,
            owner       = excluded.owner
        """,
        (job_name, command, schedule, description, owner),
    )
    conn.commit()


def get_job(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return a single catalog entry or None."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, command, schedule, description, owner, created_at "
        "FROM job_catalog WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    keys = ("job_name", "command", "schedule", "description", "owner", "created_at")
    return dict(zip(keys, row))


def list_jobs(conn: sqlite3.Connection) -> list:
    """Return all catalog entries ordered by job_name."""
    _ensure_table(conn)
    keys = ("job_name", "command", "schedule", "description", "owner", "created_at")
    rows = conn.execute(
        "SELECT job_name, command, schedule, description, owner, created_at "
        "FROM job_catalog ORDER BY job_name"
    ).fetchall()
    return [dict(zip(keys, r)) for r in rows]


def deregister_job(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove a job from the catalog. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_catalog WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0
