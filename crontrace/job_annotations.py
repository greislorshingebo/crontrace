"""Attach and retrieve free-text annotations on individual job executions."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_annotations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            exec_id     INTEGER NOT NULL,
            job_name    TEXT    NOT NULL,
            note        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ann_exec_id ON execution_annotations(exec_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_ann_job_name ON execution_annotations(job_name)"
    )
    conn.commit()


def add_annotation(conn: sqlite3.Connection, exec_id: int, job_name: str, note: str) -> int:
    """Attach *note* to the execution identified by *exec_id*.

    Returns the rowid of the newly created annotation.
    """
    _ensure_table(conn)
    if not note.strip():
        raise ValueError("Annotation note must not be empty.")
    cur = conn.execute(
        "INSERT INTO execution_annotations (exec_id, job_name, note) VALUES (?, ?, ?)",
        (exec_id, job_name, note.strip()),
    )
    conn.commit()
    return cur.lastrowid


def get_annotations(conn: sqlite3.Connection, exec_id: int) -> list[dict]:
    """Return all annotations for a given execution, oldest first."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT id, exec_id, job_name, note, created_at "
        "FROM execution_annotations WHERE exec_id = ? ORDER BY id",
        (exec_id,),
    ).fetchall()
    return [
        {"id": r[0], "exec_id": r[1], "job_name": r[2], "note": r[3], "created_at": r[4]}
        for r in rows
    ]


def delete_annotation(conn: sqlite3.Connection, annotation_id: int) -> bool:
    """Remove an annotation by its id.  Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM execution_annotations WHERE id = ?", (annotation_id,)
    )
    conn.commit()
    return cur.rowcount > 0


def annotations_for_job(conn: sqlite3.Connection, job_name: str) -> list[dict]:
    """Return all annotations ever written for *job_name*, newest first."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT id, exec_id, job_name, note, created_at "
        "FROM execution_annotations WHERE job_name = ? ORDER BY id DESC",
        (job_name,),
    ).fetchall()
    return [
        {"id": r[0], "exec_id": r[1], "job_name": r[2], "note": r[3], "created_at": r[4]}
        for r in rows
    ]
