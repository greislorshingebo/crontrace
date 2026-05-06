"""CLI helpers for inspecting and clearing job locks."""

import sqlite3
from typing import List, Optional

from crontrace.job_lock import get_lock_info, is_locked, release_lock, _ensure_table


def list_locks(conn: sqlite3.Connection) -> List[dict]:
    """Return all active lock rows as a list of dicts."""
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT job_name, pid, acquired FROM job_locks ORDER BY acquired"
    ).fetchall()
    return [{"job_name": r[0], "pid": r[1], "acquired": r[2]} for r in rows]


def force_release(conn: sqlite3.Connection, job_name: str) -> bool:
    """Forcibly remove a lock regardless of which process holds it.

    Returns True if a lock was present and removed, False otherwise.
    """
    if not is_locked(conn, job_name):
        return False
    release_lock(conn, job_name)
    return True


def render_lock_table(locks: List[dict]) -> str:
    """Format a list of lock dicts into a human-readable table string."""
    if not locks:
        return "No active locks."
    header = f"{'JOB':<30} {'PID':>8}  {'ACQUIRED'}"
    separator = "-" * len(header)
    lines = [header, separator]
    for lock in locks:
        lines.append(
            f"{lock['job_name']:<30} {lock['pid']:>8}  {lock['acquired']}"
        )
    return "\n".join(lines)


def print_locks(conn: sqlite3.Connection) -> None:  # pragma: no cover
    """Print the active lock table to stdout."""
    print(render_lock_table(list_locks(conn)))
