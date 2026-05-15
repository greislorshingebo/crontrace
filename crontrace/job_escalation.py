"""Escalation policy storage for cron jobs.

An escalation policy defines how many consecutive failures must occur
before an alert is raised, and optionally a contact to notify.
"""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_escalation (
            job_name  TEXT PRIMARY KEY,
            threshold INTEGER NOT NULL DEFAULT 3,
            contact   TEXT,
            enabled   INTEGER NOT NULL DEFAULT 1,
            note      TEXT
        )
        """
    )
    conn.commit()


def set_escalation(
    conn: sqlite3.Connection,
    job_name: str,
    threshold: int,
    contact: Optional[str] = None,
    enabled: bool = True,
    note: Optional[str] = None,
) -> None:
    """Insert or replace the escalation policy for *job_name*."""
    if threshold < 1:
        raise ValueError("threshold must be >= 1")
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_escalation (job_name, threshold, contact, enabled, note)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            threshold = excluded.threshold,
            contact   = excluded.contact,
            enabled   = excluded.enabled,
            note      = excluded.note
        """,
        (job_name, threshold, contact, int(enabled), note),
    )
    conn.commit()


def get_escalation(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the escalation policy for *job_name*, or None if absent."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, threshold, contact, enabled, note "
        "FROM job_escalation WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {
        "job_name": row[0],
        "threshold": row[1],
        "contact": row[2],
        "enabled": bool(row[3]),
        "note": row[4],
    }


def delete_escalation(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the escalation policy for *job_name*. Returns True if deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_escalation WHERE job_name = ?", (job_name,)
    )
    conn.commit()
    return cur.rowcount > 0


def list_escalations(conn: sqlite3.Connection) -> list:
    """Return all escalation policies ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, threshold, contact, enabled, note "
        "FROM job_escalation ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "threshold": r[1], "contact": r[2],
         "enabled": bool(r[3]), "note": r[4]}
        for r in rows
    ]


def is_escalated(conn: sqlite3.Connection, job_name: str, consecutive_failures: int) -> bool:
    """Return True when *consecutive_failures* meets or exceeds the policy threshold."""
    policy = get_escalation(conn, job_name)
    if policy is None or not policy["enabled"]:
        return False
    return consecutive_failures >= policy["threshold"]
