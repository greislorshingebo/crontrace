"""Blackout windows: suppress job execution during defined time ranges."""

import sqlite3
from datetime import datetime, time
from typing import Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_blackouts (
            job_name  TEXT NOT NULL,
            label     TEXT NOT NULL DEFAULT '',
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            days_of_week TEXT NOT NULL DEFAULT '*',
            PRIMARY KEY (job_name, label)
        )
        """
    )
    conn.commit()


def set_blackout(
    conn: sqlite3.Connection,
    job_name: str,
    start_time: str,
    end_time: str,
    label: str = "default",
    days_of_week: str = "*",
) -> None:
    """Insert or replace a blackout window for a job.

    start_time / end_time are 'HH:MM' strings (24-hour).
    days_of_week is '*' or a comma-separated list of day abbreviations,
    e.g. 'Mon,Tue,Wed'.
    """
    _ensure_table(conn)
    conn.execute(
        """
        INSERT INTO job_blackouts (job_name, label, start_time, end_time, days_of_week)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(job_name, label) DO UPDATE SET
            start_time   = excluded.start_time,
            end_time     = excluded.end_time,
            days_of_week = excluded.days_of_week
        """,
        (job_name, label, start_time, end_time, days_of_week),
    )
    conn.commit()


def get_blackout(conn: sqlite3.Connection, job_name: str, label: str = "default") -> Optional[dict]:
    """Return the blackout row for (job_name, label) or None."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT job_name, label, start_time, end_time, days_of_week "
        "FROM job_blackouts WHERE job_name = ? AND label = ?",
        (job_name, label),
    ).fetchone()
    if row is None:
        return None
    return dict(zip(["job_name", "label", "start_time", "end_time", "days_of_week"], row))


def delete_blackout(conn: sqlite3.Connection, job_name: str, label: str = "default") -> None:
    """Remove a specific blackout window."""
    _ensure_table(conn)
    conn.execute(
        "DELETE FROM job_blackouts WHERE job_name = ? AND label = ?",
        (job_name, label),
    )
    conn.commit()


def list_blackouts(conn: sqlite3.Connection, job_name: str) -> list:
    """Return all blackout windows for a job, ordered by label."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, label, start_time, end_time, days_of_week "
        "FROM job_blackouts WHERE job_name = ? ORDER BY label",
        (job_name,),
    ).fetchall()
    keys = ["job_name", "label", "start_time", "end_time", "days_of_week"]
    return [dict(zip(keys, r)) for r in rows]


def is_blacked_out(conn: sqlite3.Connection, job_name: str, at: Optional[datetime] = None) -> bool:
    """Return True if *any* blackout window covers the given datetime (default: now UTC)."""
    _ensure_table(conn)
    if at is None:
        at = datetime.utcnow()
    day_abbr = at.strftime("%a")  # 'Mon', 'Tue', …
    current = at.time().replace(second=0, microsecond=0)
    windows = list_blackouts(conn, job_name)
    for w in windows:
        days = w["days_of_week"]
        if days != "*" and day_abbr not in [d.strip() for d in days.split(",")]:
            continue
        try:
            h1, m1 = map(int, w["start_time"].split(":"))
            h2, m2 = map(int, w["end_time"].split(":"))
        except ValueError:
            continue
        if time(h1, m1) <= current <= time(h2, m2):
            return True
    return False
