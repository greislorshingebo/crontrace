"""Track dependencies between cron jobs (job A must succeed before job B runs)."""

import sqlite3
from typing import List, Optional, Tuple


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_dependencies (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name  TEXT NOT NULL,
            depends_on TEXT NOT NULL,
            UNIQUE(job_name, depends_on)
        )
        """
    )
    conn.commit()


def add_dependency(conn: sqlite3.Connection, job_name: str, depends_on: str) -> None:
    """Register that *job_name* depends on *depends_on* completing successfully."""
    if job_name == depends_on:
        raise ValueError("A job cannot depend on itself.")
    _ensure_table(conn)
    conn.execute(
        "INSERT OR IGNORE INTO job_dependencies (job_name, depends_on) VALUES (?, ?)",
        (job_name, depends_on),
    )
    conn.commit()


def remove_dependency(conn: sqlite3.Connection, job_name: str, depends_on: str) -> bool:
    """Remove a dependency. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_dependencies WHERE job_name = ? AND depends_on = ?",
        (job_name, depends_on),
    )
    conn.commit()
    return cur.rowcount > 0


def list_dependencies(conn: sqlite3.Connection, job_name: str) -> List[str]:
    """Return all jobs that *job_name* depends on."""
    _ensure_table(conn)
    cur = conn.execute(
        "SELECT depends_on FROM job_dependencies WHERE job_name = ? ORDER BY depends_on",
        (job_name,),
    )
    return [row[0] for row in cur.fetchall()]


def dependents_of(conn: sqlite3.Connection, depends_on: str) -> List[str]:
    """Return all jobs that depend on *depends_on*."""
    _ensure_table(conn)
    cur = conn.execute(
        "SELECT job_name FROM job_dependencies WHERE depends_on = ? ORDER BY job_name",
        (depends_on,),
    )
    return [row[0] for row in cur.fetchall()]


def dependencies_satisfied(conn: sqlite3.Connection, job_name: str) -> Tuple[bool, List[str]]:
    """Check whether all dependencies of *job_name* have a last run with exit_code 0.

    Returns (satisfied, list_of_blocking_jobs).
    """
    deps = list_dependencies(conn, job_name)
    if not deps:
        return True, []

    blocking: List[str] = []
    for dep in deps:
        cur = conn.execute(
            """
            SELECT exit_code FROM executions
            WHERE job_name = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (dep,),
        )
        row = cur.fetchone()
        if row is None or row[0] != 0:
            blocking.append(dep)

    return len(blocking) == 0, blocking
