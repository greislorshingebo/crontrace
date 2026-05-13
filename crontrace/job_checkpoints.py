"""Checkpoint tracking: record named milestones within a job run."""

import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_checkpoints (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name  TEXT    NOT NULL,
            run_id    TEXT    NOT NULL,
            name      TEXT    NOT NULL,
            reached_at TEXT   NOT NULL,
            note      TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_cp_job_run ON job_checkpoints (job_name, run_id)"
    )
    conn.commit()


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_checkpoint(
    conn: sqlite3.Connection,
    job_name: str,
    run_id: str,
    name: str,
    note: Optional[str] = None,
) -> int:
    """Record a named checkpoint for a job run. Returns the new row id."""
    _ensure_table(conn)
    cur = conn.execute(
        """
        INSERT INTO job_checkpoints (job_name, run_id, name, reached_at, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (job_name, run_id, name, _utcnow(), note),
    )
    conn.commit()
    return cur.lastrowid


def get_checkpoints(conn: sqlite3.Connection, job_name: str, run_id: str) -> list:
    """Return all checkpoints for a specific job run, ordered oldest first."""
    _ensure_table(conn)
    cur = conn.execute(
        """
        SELECT id, job_name, run_id, name, reached_at, note
        FROM job_checkpoints
        WHERE job_name = ? AND run_id = ?
        ORDER BY id ASC
        """,
        (job_name, run_id),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def delete_checkpoint(conn: sqlite3.Connection, checkpoint_id: int) -> bool:
    """Delete a checkpoint by id. Returns True if a row was removed."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_checkpoints WHERE id = ?", (checkpoint_id,)
    )
    conn.commit()
    return cur.rowcount > 0


def checkpoints_for_job(conn: sqlite3.Connection, job_name: str) -> list:
    """Return all checkpoints across all runs for a job, newest run first."""
    _ensure_table(conn)
    cur = conn.execute(
        """
        SELECT id, job_name, run_id, name, reached_at, note
        FROM job_checkpoints
        WHERE job_name = ?
        ORDER BY id DESC
        """,
        (job_name,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
