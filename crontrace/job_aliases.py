"""Manage human-friendly aliases for job names."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_aliases (
            alias   TEXT PRIMARY KEY,
            job_name TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_alias(conn: sqlite3.Connection, alias: str, job_name: str) -> None:
    """Map *alias* to *job_name*, overwriting any existing mapping."""
    _ensure_table(conn)
    alias = alias.strip().lower()
    conn.execute(
        "INSERT INTO job_aliases (alias, job_name) VALUES (?, ?)"
        " ON CONFLICT(alias) DO UPDATE SET job_name = excluded.job_name",
        (alias, job_name),
    )
    conn.commit()


def get_alias(conn: sqlite3.Connection, alias: str) -> Optional[str]:
    """Return the job_name for *alias*, or None if not found."""
    _ensure_table(conn)
    alias = alias.strip().lower()
    row = conn.execute(
        "SELECT job_name FROM job_aliases WHERE alias = ?", (alias,)
    ).fetchone()
    return row[0] if row else None


def delete_alias(conn: sqlite3.Connection, alias: str) -> bool:
    """Remove *alias*. Returns True if a row was deleted, False otherwise."""
    _ensure_table(conn)
    alias = alias.strip().lower()
    cur = conn.execute("DELETE FROM job_aliases WHERE alias = ?", (alias,))
    conn.commit()
    return cur.rowcount > 0


def list_aliases(conn: sqlite3.Connection) -> list[dict]:
    """Return all aliases ordered alphabetically."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT alias, job_name FROM job_aliases ORDER BY alias"
    ).fetchall()
    return [{"alias": r[0], "job_name": r[1]} for r in rows]


def aliases_for_job(conn: sqlite3.Connection, job_name: str) -> list[str]:
    """Return all aliases that point to *job_name*."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT alias FROM job_aliases WHERE job_name = ? ORDER BY alias",
        (job_name,),
    ).fetchall()
    return [r[0] for r in rows]
