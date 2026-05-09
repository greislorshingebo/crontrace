"""Pre/post execution hooks stored per job."""

import sqlite3
from typing import Optional

VALID_HOOK_TYPES = ("pre", "post")


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_hooks (
            job_name  TEXT    NOT NULL,
            hook_type TEXT    NOT NULL CHECK(hook_type IN ('pre', 'post')),
            command   TEXT    NOT NULL,
            enabled   INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (job_name, hook_type)
        )
        """
    )
    conn.commit()


def set_hook(
    conn: sqlite3.Connection,
    job_name: str,
    hook_type: str,
    command: str,
    enabled: bool = True,
) -> None:
    """Insert or replace a hook for a job."""
    if hook_type not in VALID_HOOK_TYPES:
        raise ValueError(f"hook_type must be one of {VALID_HOOK_TYPES}")
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_hooks (job_name, hook_type, command, enabled)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name, hook_type) DO UPDATE SET
            command = excluded.command,
            enabled = excluded.enabled
        """,
        (job_name, hook_type, command, int(enabled)),
    )
    conn.commit()


def get_hook(
    conn: sqlite3.Connection, job_name: str, hook_type: str
) -> Optional[dict]:
    """Return the hook dict or None if not set."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, hook_type, command, enabled FROM job_hooks "
        "WHERE job_name = ? AND hook_type = ?",
        (job_name, hook_type),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "hook_type": row[1], "command": row[2], "enabled": bool(row[3])}


def delete_hook(conn: sqlite3.Connection, job_name: str, hook_type: str) -> None:
    """Remove a hook for a job."""
    _ensure_table(conn)
    conn.execute(
        "DELETE FROM job_hooks WHERE job_name = ? AND hook_type = ?",
        (job_name, hook_type),
    )
    conn.commit()


def list_hooks(conn: sqlite3.Connection, job_name: str) -> list:
    """Return all hooks for a job ordered by hook_type."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, hook_type, command, enabled FROM job_hooks "
        "WHERE job_name = ? ORDER BY hook_type",
        (job_name,),
    ).fetchall()
    return [
        {"job_name": r[0], "hook_type": r[1], "command": r[2], "enabled": bool(r[3])}
        for r in rows
    ]
