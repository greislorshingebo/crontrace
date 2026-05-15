"""Job watcher registry: track which users/channels are watching a job."""

import sqlite3
from typing import List, Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_watchers (
            job_name  TEXT    NOT NULL,
            watcher   TEXT    NOT NULL,
            notify_on TEXT    NOT NULL DEFAULT 'failure',
            added_at  TEXT    NOT NULL,
            PRIMARY KEY (job_name, watcher)
        )
        """
    )
    conn.commit()


def add_watcher(
    conn: sqlite3.Connection,
    job_name: str,
    watcher: str,
    notify_on: str = "failure",
) -> None:
    """Register *watcher* for *job_name*. notify_on: 'failure', 'success', 'always'."""
    if notify_on not in ("failure", "success", "always"):
        raise ValueError(f"Invalid notify_on value: {notify_on!r}")
    _ensure_table(conn)
    from crontrace.runner import _now_utc
    conn.execute(
        """
        INSERT INTO job_watchers (job_name, watcher, notify_on, added_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(job_name, watcher) DO UPDATE SET notify_on=excluded.notify_on
        """,
        (job_name, watcher.strip().lower(), notify_on, _now_utc()),
    )
    conn.commit()


def remove_watcher(conn: sqlite3.Connection, job_name: str, watcher: str) -> bool:
    """Remove a watcher. Returns True if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_watchers WHERE job_name=? AND watcher=?",
        (job_name, watcher.strip().lower()),
    )
    conn.commit()
    return cur.rowcount > 0


def list_watchers(conn: sqlite3.Connection, job_name: str) -> List[dict]:
    """Return all watchers for *job_name*, ordered alphabetically."""
    _ensure_table(conn)
    cur = conn.execute(
        "SELECT job_name, watcher, notify_on, added_at FROM job_watchers WHERE job_name=? ORDER BY watcher",
        (job_name,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def watchers_for_event(
    conn: sqlite3.Connection, job_name: str, event: str
) -> List[str]:
    """Return watcher identifiers that should be notified for *event* ('failure'|'success')."""
    _ensure_table(conn)
    cur = conn.execute(
        "SELECT watcher FROM job_watchers WHERE job_name=? AND (notify_on=? OR notify_on='always') ORDER BY watcher",
        (job_name, event),
    )
    return [row[0] for row in cur.fetchall()]
