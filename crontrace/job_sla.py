"""SLA (Service Level Agreement) tracking for cron jobs.

Stores expected maximum duration and success-rate thresholds per job,
and evaluates whether recent executions are meeting those targets.
"""

from __future__ import annotations

import sqlite3
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_sla (
            job_name      TEXT PRIMARY KEY,
            max_duration  REAL NOT NULL,
            min_success_rate REAL NOT NULL DEFAULT 1.0,
            note          TEXT
        )
        """
    )
    conn.commit()


def set_sla(
    conn: sqlite3.Connection,
    job_name: str,
    max_duration: float,
    min_success_rate: float = 1.0,
    note: Optional[str] = None,
) -> None:
    """Insert or replace the SLA definition for *job_name*."""
    _ensure_table(conn)
    if not (0.0 <= min_success_rate <= 1.0):
        raise ValueError("min_success_rate must be between 0.0 and 1.0")
    if max_duration <= 0:
        raise ValueError("max_duration must be positive")
    conn.execute(
        """
        INSERT INTO job_sla (job_name, max_duration, min_success_rate, note)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name) DO UPDATE SET
            max_duration     = excluded.max_duration,
            min_success_rate = excluded.min_success_rate,
            note             = excluded.note
        """,
        (job_name, max_duration, min_success_rate, note),
    )
    conn.commit()


def get_sla(conn: sqlite3.Connection, job_name: str) -> Optional[dict]:
    """Return the SLA dict for *job_name*, or None if not configured."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, max_duration, min_success_rate, note FROM job_sla WHERE job_name = ?",
        (job_name,),
    ).fetchone()
    if row is None:
        return None
    return dict(zip(("job_name", "max_duration", "min_success_rate", "note"), row))


def delete_sla(conn: sqlite3.Connection, job_name: str) -> bool:
    """Remove the SLA for *job_name*. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute("DELETE FROM job_sla WHERE job_name = ?", (job_name,))
    conn.commit()
    return cur.rowcount > 0


def list_slas(conn: sqlite3.Connection) -> list[dict]:
    """Return all SLA definitions ordered by job name."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, max_duration, min_success_rate, note FROM job_sla ORDER BY job_name"
    ).fetchall()
    keys = ("job_name", "max_duration", "min_success_rate", "note")
    return [dict(zip(keys, r)) for r in rows]


def evaluate_sla(sla: dict, rows: list) -> dict:
    """Evaluate *rows* (execution records) against *sla*.

    Each row must support index access: row[3] = exit_code, row[4] = duration.
    Returns a dict with keys: duration_ok, success_rate_ok, success_rate, avg_duration.
    """
    if not rows:
        return {"duration_ok": True, "success_rate_ok": True, "success_rate": None, "avg_duration": None}
    durations = [r[4] for r in rows if r[4] is not None]
    avg_dur = sum(durations) / len(durations) if durations else 0.0
    successes = sum(1 for r in rows if r[3] == 0)
    rate = successes / len(rows)
    return {
        "duration_ok": avg_dur <= sla["max_duration"],
        "success_rate_ok": rate >= sla["min_success_rate"],
        "success_rate": round(rate, 4),
        "avg_duration": round(avg_dur, 3),
    }
