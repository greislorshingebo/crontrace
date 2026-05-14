"""Snapshot the current state of a job's last execution for diffing or auditing."""

import json
import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_snapshots (
            job_name  TEXT PRIMARY KEY,
            exit_code INTEGER,
            duration  REAL,
            stdout    TEXT,
            captured_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def save_snapshot(
    conn: sqlite3.Connection,
    job_name: str,
    exit_code: int,
    duration: Optional[float],
    stdout: Optional[str],
    captured_at: str,
) -> None:
    """Insert or replace the snapshot for *job_name*."""
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_snapshots (job_name, exit_code, duration, stdout, captured_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            exit_code   = excluded.exit_code,
            duration    = excluded.duration,
            stdout      = excluded.stdout,
            captured_at = excluded.captured_at
        """,
        (job_name, exit_code, duration, stdout, captured_at),
    )
    conn.commit()


def get_snapshot(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the stored snapshot for *job_name*, or ``None`` if absent."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, exit_code, duration, stdout, captured_at "
        "FROM job_snapshots WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {
        "job_name": row[0],
        "exit_code": row[1],
        "duration": row[2],
        "stdout": row[3],
        "captured_at": row[4],
    }


def delete_snapshot(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the snapshot for *job_name*.  Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_snapshots WHERE job_name = ?", (job_name,)
    )
    conn.commit()
    return cur.rowcount > 0


def list_snapshots(conn: sqlite3.Connection) -> list:
    """Return all stored snapshots ordered by job_name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, exit_code, duration, stdout, captured_at "
        "FROM job_snapshots ORDER BY job_name"
    ).fetchall()
    return [
        {
            "job_name": r[0],
            "exit_code": r[1],
            "duration": r[2],
            "stdout": r[3],
            "captured_at": r[4],
        }
        for r in rows
    ]
