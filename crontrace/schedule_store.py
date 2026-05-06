"""Persistence helpers for storing named job schedules in the crontrace DB."""

from __future__ import annotations

import sqlite3
from typing import Optional

from crontrace.storage import get_connection


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_schedules (
            job_name  TEXT PRIMARY KEY,
            expression TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def upsert_schedule(db_path: str, job_name: str, expression: str) -> None:
    """Insert or replace the cron *expression* for *job_name*."""
    with get_connection(db_path) as conn:
        _ensure_table(conn)
        conn.execute(
            """
            INSERT INTO job_schedules (job_name, expression)
            VALUES (?, ?)
            ON CONFLICT(job_name) DO UPDATE SET expression = excluded.expression
            """,
            (job_name, expression),
        )
        conn.commit()


def fetch_schedule(db_path: str, job_name: str) -> Optional[str]:
    """Return the stored cron expression for *job_name*, or ``None``."""
    with get_connection(db_path) as conn:
        _ensure_table(conn)
        row = conn.execute(
            "SELECT expression FROM job_schedules WHERE job_name = ?",
            (job_name,),
        ).fetchone()
    return row[0] if row else None


def list_schedules(db_path: str) -> list[dict]:
    """Return all stored schedules as a list of dicts."""
    with get_connection(db_path) as conn:
        _ensure_table(conn)
        rows = conn.execute(
            "SELECT job_name, expression, created_at FROM job_schedules ORDER BY job_name"
        ).fetchall()
    return [
        {"job_name": r[0], "expression": r[1], "created_at": r[2]}
        for r in rows
    ]


def delete_schedule(db_path: str, job_name: str) -> bool:
    """Remove the schedule for *job_name*.  Returns ``True`` if a row was deleted."""
    with get_connection(db_path) as conn:
        _ensure_table(conn)
        cur = conn.execute(
            "DELETE FROM job_schedules WHERE job_name = ?", (job_name,)
        )
        conn.commit()
    return cur.rowcount > 0
