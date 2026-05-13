"""Track ownership (owner, team, contact) for registered cron jobs."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_ownership (
            job_name  TEXT PRIMARY KEY,
            owner     TEXT NOT NULL DEFAULT '',
            team      TEXT NOT NULL DEFAULT '',
            contact   TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_ownership(
    conn: sqlite3.Connection,
    job_name: str,
    owner: str = "",
    team: str = "",
    contact: str = "",
) -> None:
    """Insert or replace ownership record for *job_name*."""
    _ensure_table(conn)
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        """
        INSERT INTO job_ownership (job_name, owner, team, contact, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            owner      = excluded.owner,
            team       = excluded.team,
            contact    = excluded.contact,
            updated_at = excluded.updated_at
        """,
        (job_name, owner.strip(), team.strip(), contact.strip(), now),
    )
    conn.commit()


def get_ownership(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return ownership dict for *job_name*, or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, owner, team, contact, updated_at FROM job_ownership WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {
        "job_name": row[0],
        "owner": row[1],
        "team": row[2],
        "contact": row[3],
        "updated_at": row[4],
    }


def delete_ownership(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove ownership record; returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_ownership WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0


def list_ownership(conn: sqlite3.Connection) -> list:
    """Return all ownership records ordered by job_name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, owner, team, contact, updated_at FROM job_ownership ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "owner": r[1], "team": r[2], "contact": r[3], "updated_at": r[4]}
        for r in rows
    ]
