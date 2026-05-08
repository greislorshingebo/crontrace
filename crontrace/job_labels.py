"""Key-value label store for cron jobs.

Labels differ from tags in that they carry a value (e.g. team=backend,
env=prod) and are useful for filtering and grouping jobs by arbitrary
metadata.
"""

import sqlite3
from typing import Dict, List, Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_labels (
            job_name TEXT NOT NULL,
            key      TEXT NOT NULL,
            value    TEXT NOT NULL,
            PRIMARY KEY (job_name, key)
        )
        """
    )
    conn.commit()


def set_label(conn: sqlite3.Connection, job_name: str, key: str, value: str) -> None:
    """Insert or replace a single label for *job_name*."""
    _ensure_table(conn)
    conn.execute(
        "INSERT OR REPLACE INTO job_labels (job_name, key, value) VALUES (?, ?, ?)",
        (job_name, key.strip().lower(), value.strip()),
    )
    conn.commit()


def set_labels_bulk(conn: sqlite3.Connection, job_name: str, labels: Dict[str, str]) -> None:
    """Set multiple labels at once, overwriting any existing keys."""
    _ensure_table(conn)
    conn.executemany(
        "INSERT OR REPLACE INTO job_labels (job_name, key, value) VALUES (?, ?, ?)",
        [(job_name, k.strip().lower(), v.strip()) for k, v in labels.items()],
    )
    conn.commit()


def get_label(conn: sqlite3.Connection, job_name: str, key: str) -> Optional[str]:
    """Return the value for *key* on *job_name*, or ``None`` if absent."""
    _ensure_table(conn)
    row = conn.execute(
        "SELECT value FROM job_labels WHERE job_name = ? AND key = ?",
        (job_name, key.strip().lower()),
    ).fetchone()
    return row[0] if row else None


def get_labels(conn: sqlite3.Connection, job_name: str) -> Dict[str, str]:
    """Return all labels for *job_name* as a ``{key: value}`` dict."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT key, value FROM job_labels WHERE job_name = ? ORDER BY key",
        (job_name,),
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def delete_label(conn: sqlite3.Connection, job_name: str, key: str) -> bool:
    """Remove a single label.  Returns ``True`` if a row was deleted."""
    _ensure_table(conn)
    cur = conn.execute(
        "DELETE FROM job_labels WHERE job_name = ? AND key = ?",
        (job_name, key.strip().lower()),
    )
    conn.commit()
    return cur.rowcount > 0


def jobs_by_label(conn: sqlite3.Connection, key: str, value: str) -> List[str]:
    """Return job names that have the given *key=value* label."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT DISTINCT job_name FROM job_labels WHERE key = ? AND value = ? ORDER BY job_name",
        (key.strip().lower(), value.strip()),
    ).fetchall()
    return [r[0] for r in rows]
