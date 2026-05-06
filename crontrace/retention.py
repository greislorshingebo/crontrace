"""Retention policy helpers: compute storage stats and enforce size-based limits."""

from __future__ import annotations

import sqlite3
from typing import Dict, Any


def get_storage_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Return row count and oldest/newest timestamps for the executions table."""
    cur = conn.execute(
        "SELECT COUNT(*), MIN(started_at), MAX(started_at) FROM executions"
    )
    row = cur.fetchone()
    count, oldest, newest = row if row else (0, None, None)
    return {
        "total_rows": count or 0,
        "oldest": oldest,
        "newest": newest,
    }


def enforce_row_limit(conn: sqlite3.Connection, max_rows: int) -> int:
    """Delete oldest rows so that at most *max_rows* records remain.

    Returns the number of rows deleted.
    """
    if max_rows <= 0:
        raise ValueError("max_rows must be a positive integer")

    stats = get_storage_stats(conn)
    total = stats["total_rows"]
    excess = total - max_rows
    if excess <= 0:
        return 0

    conn.execute(
        """
        DELETE FROM executions
        WHERE rowid IN (
            SELECT rowid FROM executions
            ORDER BY started_at ASC
            LIMIT ?
        )
        """,
        (excess,),
    )
    conn.commit()
    return excess


def retention_summary(conn: sqlite3.Connection, max_rows: int) -> Dict[str, Any]:
    """Return a human-readable summary dict of current retention state."""
    stats = get_storage_stats(conn)
    over = max(0, stats["total_rows"] - max_rows)
    return {
        **stats,
        "max_rows": max_rows,
        "rows_over_limit": over,
        "within_limit": over == 0,
    }
