"""Tests for crontrace.retention."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone, timedelta

import pytest

from crontrace.retention import enforce_row_limit, get_storage_stats, retention_summary


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.execute(
        """
        CREATE TABLE executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            started_at TEXT,
            duration_s REAL,
            exit_code INTEGER
        )
        """
    )
    c.commit()
    return c


def _ts(offset_minutes: int = 0) -> str:
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=offset_minutes)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _insert(conn: sqlite3.Connection, n: int) -> None:
    for i in range(n):
        conn.execute(
            "INSERT INTO executions (job_name, started_at, duration_s, exit_code) VALUES (?,?,?,?)",
            ("job", _ts(i), 1.0, 0),
        )
    conn.commit()


def test_get_storage_stats_empty(conn):
    stats = get_storage_stats(conn)
    assert stats["total_rows"] == 0
    assert stats["oldest"] is None
    assert stats["newest"] is None


def test_get_storage_stats_with_rows(conn):
    _insert(conn, 5)
    stats = get_storage_stats(conn)
    assert stats["total_rows"] == 5
    assert stats["oldest"] is not None
    assert stats["newest"] is not None
    assert stats["oldest"] < stats["newest"]


def test_enforce_row_limit_no_op_when_under(conn):
    _insert(conn, 3)
    deleted = enforce_row_limit(conn, max_rows=10)
    assert deleted == 0
    assert get_storage_stats(conn)["total_rows"] == 3


def test_enforce_row_limit_removes_excess(conn):
    _insert(conn, 10)
    deleted = enforce_row_limit(conn, max_rows=6)
    assert deleted == 4
    assert get_storage_stats(conn)["total_rows"] == 6


def test_enforce_row_limit_removes_oldest(conn):
    _insert(conn, 5)
    enforce_row_limit(conn, max_rows=3)
    rows = conn.execute("SELECT started_at FROM executions ORDER BY started_at").fetchall()
    assert len(rows) == 3
    # The two oldest rows (offset 0 and 1) should be gone; offset 2 is now oldest
    assert rows[0][0] == _ts(2)


def test_enforce_row_limit_invalid_max_rows(conn):
    with pytest.raises(ValueError):
        enforce_row_limit(conn, max_rows=0)


def test_retention_summary_within_limit(conn):
    _insert(conn, 4)
    summary = retention_summary(conn, max_rows=10)
    assert summary["within_limit"] is True
    assert summary["rows_over_limit"] == 0
    assert summary["max_rows"] == 10


def test_retention_summary_over_limit(conn):
    _insert(conn, 15)
    summary = retention_summary(conn, max_rows=10)
    assert summary["within_limit"] is False
    assert summary["rows_over_limit"] == 5
