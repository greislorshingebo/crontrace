"""Per-job runbook links: store and retrieve URLs pointing to
operational runbooks or documentation for a given job."""

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_runbooks (
            job_name  TEXT PRIMARY KEY,
            url       TEXT NOT NULL,
            note      TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def set_runbook(
    conn: sqlite3.Connection,
    job_name: str,
    url: str,
    note: Optional[str] = None,
) -> None:
    """Insert or replace the runbook entry for *job_name*."""
    _ensure_table(conn)
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        """
        INSERT INTO job_runbooks (job_name, url, note, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            url        = excluded.url,
            note       = excluded.note,
            updated_at = excluded.updated_at
        """,
        (job_name.strip(), url.strip(), note, now),
    )
    conn.commit()


def get_runbook(
    conn: sqlite3.Connection, job_name: str
) -> Optional[dict]:
    """Return the runbook dict for *job_name*, or ``None`` if absent."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, url, note, updated_at FROM job_runbooks WHERE job_name = ?",
        (job_name.strip(),),
    ).fetchone()
    if row is None:
        return None
    return {"job_name": row[0], "url": row[1], "note": row[2], "updated_at": row[3]}


def delete_runbook(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the runbook entry for *job_name*.  Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_runbooks WHERE job_name = ?", (job_name.strip(),)
    )
    conn.commit()
    return cur.rowcount > 0


def list_runbooks(conn: sqlite3.Connection) -> list:
    """Return all runbook entries ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, url, note, updated_at FROM job_runbooks ORDER BY job_name"
    ).fetchall()
    return [
        {"job_name": r[0], "url": r[1], "note": r[2], "updated_at": r[3]}
        for r in rows
    ]
