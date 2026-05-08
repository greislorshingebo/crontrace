"""Job priority management — assign and query execution priorities."""

import sqlite3
from typing import Optional

VALID_PRIORITIES = ("low", "normal", "high", "critical")
DEFAULT_PRIORITY = "normal"


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_priority (
            job_name  TEXT PRIMARY KEY,
            priority  TEXT NOT NULL DEFAULT 'normal',
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_priority(conn: sqlite3.Connection, job_name: str, priority: str) -> None:
    """Set the priority for a job. Raises ValueError for unknown priorities."""
    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority {priority!r}. Choose from: {', '.join(VALID_PRIORITIES)}"
        )
    _ensure_table(conn)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO job_priority (job_name, priority, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET priority = excluded.priority,
                                             updated_at = excluded.updated_at
        """,
        (job_name, priority, now),
    )
    conn.commit()


def get_priority(conn: sqlite3.Connection, job_name: str) -> str:
    """Return the priority for a job, or DEFAULT_PRIORITY if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT priority FROM job_priority WHERE job_name = ?", (job_name,)
    ).fetchone()
    return row[0] if row else DEFAULT_PRIORITY


def delete_priority(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove a job's priority entry. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_priority WHERE job_name = ?", (job_name,)
    )
    conn.commit()
    return cur.rowcount > 0


def list_priorities(conn: sqlite3.Connection) -> list:
    """Return all (job_name, priority, updated_at) rows ordered by priority rank."""
    _ensure_table(conn)
    rank = " ".join(
        f"WHEN '{p}' THEN {i}" for i, p in enumerate(reversed(VALID_PRIORITIES))
    )
    rows = conn.execute(
        f"""
        SELECT job_name, priority, updated_at
        FROM job_priority
        ORDER BY CASE priority {rank} ELSE 99 END, job_name
        """
    ).fetchall()
    return [dict(zip(("job_name", "priority", "updated_at"), r)) for r in rows]
