"""SQLite-backed storage for cron job execution records."""

import sqlite3
import os
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".crontrace" / "history.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS executions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_name    TEXT    NOT NULL,
    command     TEXT    NOT NULL,
    started_at  TEXT    NOT NULL,
    finished_at TEXT    NOT NULL,
    duration_s  REAL    NOT NULL,
    exit_code   INTEGER NOT NULL
);
"""


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (and initialise) the SQLite database, returning a connection."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    return conn


def insert_execution(conn: sqlite3.Connection, record: dict) -> int:
    """Persist a single execution record; returns the new row id."""
    sql = """
    INSERT INTO executions
        (job_name, command, started_at, finished_at, duration_s, exit_code)
    VALUES
        (:job_name, :command, :started_at, :finished_at, :duration_s, :exit_code)
    """
    cursor = conn.execute(sql, record)
    conn.commit()
    return cursor.lastrowid


def fetch_recent(conn: sqlite3.Connection, job_name: str | None = None, limit: int = 20) -> list:
    """Return the most recent execution rows, optionally filtered by job name."""
    if job_name:
        sql = (
            "SELECT * FROM executions WHERE job_name = ? "
            "ORDER BY id DESC LIMIT ?"
        )
        rows = conn.execute(sql, (job_name, limit)).fetchall()
    else:
        sql = "SELECT * FROM executions ORDER BY id DESC LIMIT ?"
        rows = conn.execute(sql, (limit,)).fetchall()
    return [dict(r) for r in rows]
