"""Manage manual and event-based trigger records for cron jobs."""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

TRIGGER_TYPES = ("manual", "dependency", "webhook", "schedule")


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_triggers (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name  TEXT    NOT NULL,
            trigger   TEXT    NOT NULL,
            note      TEXT,
            fired_at  TEXT    NOT NULL
        )
        """
    )
    conn.commit()


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_trigger(
    conn: sqlite3.Connection,
    job_name: str,
    trigger: str,
    note: Optional[str] = None,
) -> int:
    """Insert a trigger event and return its rowid."""
    if trigger not in TRIGGER_TYPES:
        raise ValueError(f"Unknown trigger type '{trigger}'. Choose from {TRIGGER_TYPES}")
    _ensure_table(conn)
    cur = conn.execute(
        "INSERT INTO job_triggers (job_name, trigger, note, fired_at) VALUES (?, ?, ?, ?)",
        (job_name, trigger, note, _utcnow()),
    )
    conn.commit()
    return cur.lastrowid


def get_triggers(
    conn: sqlite3.Connection,
    job_name: str,
    limit: int = 50,
) -> list[dict]:
    """Return recent trigger events for *job_name*, newest first."""
    _ensure_table(conn)
    rows = conn.execute(
        """
        SELECT id, job_name, trigger, note, fired_at
        FROM job_triggers
        WHERE job_name = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (job_name, limit),
    ).fetchall()
    return [
        {"id": r[0], "job_name": r[1], "trigger": r[2], "note": r[3], "fired_at": r[4]}
        for r in rows
    ]


def delete_trigger(conn: sqlite3.Connection, trigger_id: int) -> bool:
    """Delete a trigger record by id. Returns True if a row was removed."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_triggers WHERE id = ?", (trigger_id,))
    conn.commit()
    return cur.rowcount > 0


def triggers_for_type(
    conn: sqlite3.Connection,
    trigger: str,
    limit: int = 100,
) -> list[dict]:
    """Return all recent trigger events of a specific type across all jobs."""
    _ensure_table(conn)
    rows = conn.execute(
        """
        SELECT id, job_name, trigger, note, fired_at
        FROM job_triggers
        WHERE trigger = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (trigger, limit),
    ).fetchall()
    return [
        {"id": r[0], "job_name": r[1], "trigger": r[2], "note": r[3], "fired_at": r[4]}
        for r in rows
    ]
