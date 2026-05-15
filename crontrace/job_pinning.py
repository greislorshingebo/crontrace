"""Pin a specific execution as a reference baseline for a job."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_pins (
            job_name  TEXT PRIMARY KEY,
            run_id    INTEGER NOT NULL,
            note      TEXT,
            pinned_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def pin_execution(
    conn: sqlite3.Connection,
    job_name: str,
    run_id: int,
    note: Optional[str] = None,
    pinned_at: Optional[str] = None,
) -> None:
    """Pin *run_id* as the reference execution for *job_name*."""
    _ensure_table(conn)
    from crontrace.runner import _now_utc

    ts = pinned_at or _now_utc()
    conn.execute(
        """
        INSERT INTO job_pins (job_name, run_id, note, pinned_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            run_id    = excluded.run_id,
            note      = excluded.note,
            pinned_at = excluded.pinned_at
        """,
        (job_name, run_id, note, ts),
    )
    conn.commit()


def get_pin(
    conn: sqlite3.Connection, job_name: str
) -> Optional[dict]:
    """Return the pin record for *job_name*, or ``None`` if absent."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, run_id, note, pinned_at FROM job_pins WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "run_id": row[1], "note": row[2], "pinned_at": row[3]}


def unpin(
    conn: sqlite3.Connection, job_name: str
) -> bool:
    """Remove the pin for *job_name*.  Returns ``True`` if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_pins WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0


def list_pins(conn: sqlite3.Connection) -> list:
    """Return all pin records ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, run_id, note, pinned_at FROM job_pins ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "run_id": r[1], "note": r[2], "pinned_at": r[3]}
        for r in rows
    ]
