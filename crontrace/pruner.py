"""Pruner module: remove old execution records from the database."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from crontrace.storage import get_connection


def _cutoff_utc(days: int) -> str:
    """Return an ISO-8601 UTC timestamp *days* ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%S")


def prune_old_records(
    db_path: str,
    days: int,
    job_name: Optional[str] = None,
) -> int:
    """Delete execution records older than *days* days.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    days:
        Records with a ``started_at`` older than this many days are removed.
    job_name:
        When provided, only records for this specific job are pruned.

    Returns
    -------
    int
        Number of rows deleted.
    """
    if days < 1:
        raise ValueError("days must be a positive integer")

    cutoff = _cutoff_utc(days)
    conn = get_connection(db_path)
    try:
        if job_name is not None:
            cursor = conn.execute(
                "DELETE FROM executions WHERE started_at < ? AND job_name = ?",
                (cutoff, job_name),
            )
        else:
            cursor = conn.execute(
                "DELETE FROM executions WHERE started_at < ?",
                (cutoff,),
            )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()
