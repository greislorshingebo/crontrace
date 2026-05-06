"""Tag management for cron jobs — attach/remove labels and filter by tag."""

from __future__ import annotations

import sqlite3
from typing import List, Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_tags (
            job_name TEXT NOT NULL,
            tag      TEXT NOT NULL,
            PRIMARY KEY (job_name, tag)
        )
        """
    )
    conn.commit()


def add_tag(conn: sqlite3.Connection, job_name: str, tag: str) -> None:
    """Attach *tag* to *job_name*.  Silently ignores duplicates."""
    _ensure_table(conn)
    conn.execute(
        "INSERT OR IGNORE INTO job_tags (job_name, tag) VALUES (?, ?)",
        (job_name, tag.strip().lower()),
    )
    conn.commit()


def remove_tag(conn: sqlite3.Connection, job_name: str, tag: str) -> None:
    """Remove *tag* from *job_name*.  No-op if the pair does not exist."""
    _ensure_table(conn)
    conn.execute(
        "DELETE FROM job_tags WHERE job_name = ? AND tag = ?",
        (job_name, tag.strip().lower()),
    )
    conn.commit()


def list_tags(conn: sqlite3.Connection, job_name: str) -> List[str]:
    """Return all tags associated with *job_name*, sorted alphabetically."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT tag FROM job_tags WHERE job_name = ? ORDER BY tag",
        (job_name,),
    ).fetchall()
    return [r[0] for r in rows]


def jobs_by_tag(conn: sqlite3.Connection, tag: str) -> List[str]:
    """Return all job names that carry *tag*, sorted alphabetically."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name FROM job_tags WHERE tag = ? ORDER BY job_name",
        (tag.strip().lower(),),
    ).fetchall()
    return [r[0] for r in rows]


def clear_tags(conn: sqlite3.Connection, job_name: str) -> None:
    """Remove every tag associated with *job_name*."""
    _ensure_table(conn)
    conn.execute("DELETE FROM job_tags WHERE job_name = ?", (job_name,))
    conn.commit()
