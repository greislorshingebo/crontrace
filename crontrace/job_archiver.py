"""Archive completed job execution records to a separate table."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_archive (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name    TEXT NOT NULL,
            started_at  TEXT NOT NULL,
            duration    REAL,
            exit_code   INTEGER NOT NULL,
            stdout      TEXT,
            archived_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_archive_job_name ON job_archive (job_name)"
    )
    conn.commit()


def archive_executions(
    conn: sqlite3.Connection,
    job_name: str,
    older_than: str,
) -> int:
    """Move executions older than *older_than* (ISO timestamp) into the archive.

    Returns the number of rows archived.
    """
    _ensure_table(conn)
    rows = conn.execute(
        """
        SELECT job_name, started_at, duration, exit_code, stdout
        FROM   executions
        WHERE  job_name = ? AND started_at < ?
        """,
        (job_name, older_than),
    ).fetchall()

    if not rows:
        return 0

    conn.executemany(
        """
        INSERT INTO job_archive (job_name, started_at, duration, exit_code, stdout)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.execute(
        "DELETE FROM executions WHERE job_name = ? AND started_at < ?",
        (job_name, older_than),
    )
    conn.commit()
    return len(rows)


def fetch_archive(
    conn: sqlite3.Connection,
    job_name: str,
    limit: int = 50,
) -> list[dict]:
    """Return archived records for *job_name*, newest first."""
    _ensure_table(conn)
    rows = conn.execute(
        """
        SELECT id, job_name, started_at, duration, exit_code, stdout, archived_at
        FROM   job_archive
        WHERE  job_name = ?
        ORDER  BY started_at DESC
        LIMIT  ?
        """,
        (job_name, limit),
    ).fetchall()
    keys = ("id", "job_name", "started_at", "duration", "exit_code", "stdout", "archived_at")
    return [dict(zip(keys, r)) for r in rows]


def purge_archive(conn: sqlite3.Connection, job_name: Optional[str] = None) -> int:
    """Delete all archive rows, optionally filtered to *job_name*."""
    _ensure_table(conn)
    if job_name:
        cur = conn.execute("DELETE FROM job_archive WHERE job_name = ?", (job_name,))
    else:
        cur = conn.execute("DELETE FROM job_archive")
    conn.commit()
    return cur.rowcount
