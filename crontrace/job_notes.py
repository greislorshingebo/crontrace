"""Per-execution notes: attach a short text note to any execution row."""

import sqlite3
from typing import Optional, List, Dict, Any


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            exec_id     INTEGER NOT NULL,
            job_name    TEXT    NOT NULL,
            note        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_notes_exec_id ON execution_notes (exec_id)"
    )
    conn.commit()


def add_note(
    conn: sqlite3.Connection,
    exec_id: int,
    job_name: str,
    note: str,
    created_at: str,
) -> int:
    """Attach *note* to the execution identified by *exec_id*.

    Returns the new row id.
    """
    _ensure_table(conn)
    if not note or not note.strip():
        raise ValueError("note must not be empty")
    cur = conn.execute(
        """
        INSERT INTO execution_notes (exec_id, job_name, note, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (exec_id, job_name, note.strip(), created_at),
    )
    conn.commit()
    return cur.lastrowid


def get_notes(conn: sqlite3.Connection, exec_id: int) -> List[Dict[str, Any]]:
    """Return all notes for *exec_id*, ordered oldest-first."""
    _ensure_table(conn)
    cur = conn.execute(
        """
        SELECT id, exec_id, job_name, note, created_at
        FROM execution_notes
        WHERE exec_id = ?
        ORDER BY id ASC
        """,
        (exec_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def delete_note(conn: sqlite3.Connection, note_id: int) -> bool:
    """Delete a single note by its *note_id*. Returns True if a row was removed."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM execution_notes WHERE id = ?", (note_id,))
    conn.commit()
    return cur.rowcount > 0


def notes_for_job(conn: sqlite3.Connection, job_name: str) -> List[Dict[str, Any]]:
    """Return all notes across every execution for *job_name*."""
    _ensure_table(conn)
    cur = conn.execute(
        """
        SELECT id, exec_id, job_name, note, created_at
        FROM execution_notes
        WHERE job_name = ?
        ORDER BY id ASC
        """,
        (job_name,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
