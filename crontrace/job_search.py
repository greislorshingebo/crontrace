"""Full-text and field-based search over job execution history."""

from __future__ import annotations

import sqlite3
from typing import Any


_FIELDS = ("job_name", "exit_code", "stdout", "stderr")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def search_by_name(conn: sqlite3.Connection, pattern: str) -> list[dict[str, Any]]:
    """Return executions whose job_name contains *pattern* (case-insensitive)."""
    sql = """
        SELECT * FROM executions
        WHERE LOWER(job_name) LIKE LOWER(?)
        ORDER BY started_at DESC
    """
    conn.row_factory = sqlite3.Row
    cur = conn.execute(sql, (f"%{pattern}%",))
    return [_row_to_dict(r) for r in cur.fetchall()]


def search_by_exit_code(conn: sqlite3.Connection, code: int) -> list[dict[str, Any]]:
    """Return executions that finished with *code*."""
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT * FROM executions WHERE exit_code = ? ORDER BY started_at DESC",
        (code,),
    )
    return [_row_to_dict(r) for r in cur.fetchall()]


def search_output(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    """Return executions where stdout or stderr contains *term*."""
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT * FROM executions
        WHERE LOWER(stdout) LIKE LOWER(?)
           OR LOWER(stderr) LIKE LOWER(?)
        ORDER BY started_at DESC
    """
    like = f"%{term}%"
    cur = conn.execute(sql, (like, like))
    return [_row_to_dict(r) for r in cur.fetchall()]


def search_combined(
    conn: sqlite3.Connection,
    *,
    name: str | None = None,
    exit_code: int | None = None,
    output_term: str | None = None,
) -> list[dict[str, Any]]:
    """Combine multiple optional filters with AND semantics."""
    clauses: list[str] = []
    params: list[Any] = []

    if name is not None:
        clauses.append("LOWER(job_name) LIKE LOWER(?)")
        params.append(f"%{name}%")
    if exit_code is not None:
        clauses.append("exit_code = ?")
        params.append(exit_code)
    if output_term is not None:
        clauses.append("(LOWER(stdout) LIKE LOWER(?) OR LOWER(stderr) LIKE LOWER(?))")
        like = f"%{output_term}%"
        params.extend([like, like])

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM executions {where} ORDER BY started_at DESC"
    conn.row_factory = sqlite3.Row
    cur = conn.execute(sql, params)
    return [_row_to_dict(r) for r in cur.fetchall()]
