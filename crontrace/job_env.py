"""Store and retrieve per-job environment variable snapshots."""

import json
import sqlite3
from typing import Dict, List, Optional


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_env (
            job_name  TEXT NOT NULL,
            key       TEXT NOT NULL,
            value     TEXT NOT NULL,
            PRIMARY KEY (job_name, key)
        )
        """
    )
    conn.commit()


def set_env(conn: sqlite3.Connection, job_name: str, key: str, value: str) -> None:
    """Insert or replace a single environment variable for a job."""
    _ensure_table(conn)
    conn.execute(
        "INSERT OR REPLACE INTO job_env (job_name, key, value) VALUES (?, ?, ?)",
        (job_name, key, value),
    )
    conn.commit()


def set_env_bulk(conn: sqlite3.Connection, job_name: str, env: Dict[str, str]) -> None:
    """Replace all environment variables for a job in one operation."""
    _ensure_table(conn)
    conn.execute("DELETE FROM job_env WHERE job_name = ?", (job_name,))
    conn.executemany(
        "INSERT INTO job_env (job_name, key, value) VALUES (?, ?, ?)",
        [(job_name, k, v) for k, v in env.items()],
    )
    conn.commit()


def get_env(conn: sqlite3.Connection, job_name: str) -> Dict[str, str]:
    """Return all stored environment variables for *job_name* as a dict."""
    _ensure_table(conn)
    cursor = conn.execute(
        "SELECT key, value FROM job_env WHERE job_name = ? ORDER BY key",
        (job_name,),
    )
    return {row[0]: row[1] for row in cursor.fetchall()}


def delete_env_key(conn: sqlite3.Connection, job_name: str, key: str) -> bool:
    """Remove a single key.  Returns True if a row was deleted."""
    _ensure_table(conn)
    cursor = conn.execute(
        "DELETE FROM job_env WHERE job_name = ? AND key = ?",
        (job_name, key),
    )
    conn.commit()
    return cursor.rowcount > 0


def clear_env(conn: sqlite3.Connection, job_name: str) -> int:
    """Remove all env vars for *job_name*.  Returns number of rows deleted."""
    _ensure_table(conn)
    cursor = conn.execute("DELETE FROM job_env WHERE job_name = ?", (job_name,))
    conn.commit()
    return cursor.rowcount


def export_env_json(conn: sqlite3.Connection, job_name: str) -> str:
    """Return the env dict serialised as a JSON string."""
    return json.dumps(get_env(conn, job_name), indent=2)
