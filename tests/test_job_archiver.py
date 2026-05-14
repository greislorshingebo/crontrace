"""Tests for crontrace.job_archiver."""

import sqlite3
from datetime import datetime, timezone, timedelta

import pytest

from crontrace.job_archiver import (
    archive_executions,
    fetch_archive,
    purge_archive,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.execute(
        """
        CREATE TABLE executions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name   TEXT NOT NULL,
            started_at TEXT NOT NULL,
            duration   REAL,
            exit_code  INTEGER NOT NULL,
            stdout     TEXT
        )
        """
    )
    c.commit()
    return c


def _ts(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _insert(conn, job_name, days_ago, exit_code=0):
    conn.execute(
        "INSERT INTO executions (job_name, started_at, duration, exit_code, stdout) VALUES (?,?,?,?,?)",
        (job_name, _ts(days_ago), 1.0, exit_code, ""),
    )
    conn.commit()


def test_fetch_archive_empty_when_none(conn):
    rows = fetch_archive(conn, "myjob")
    assert rows == []


def test_archive_executions_returns_zero_when_nothing_matches(conn):
    _insert(conn, "myjob", 1)
    moved = archive_executions(conn, "myjob", _ts(30))
    assert moved == 0


def test_archive_executions_moves_old_rows(conn):
    _insert(conn, "myjob", 40)
    _insert(conn, "myjob", 35)
    moved = archive_executions(conn, "myjob", _ts(30))
    assert moved == 2


def test_archive_executions_removes_from_executions(conn):
    _insert(conn, "myjob", 40)
    archive_executions(conn, "myjob", _ts(30))
    remaining = conn.execute(
        "SELECT COUNT(*) FROM executions WHERE job_name='myjob'"
    ).fetchone()[0]
    assert remaining == 0


def test_archive_executions_preserves_recent_rows(conn):
    _insert(conn, "myjob", 40)  # old
    _insert(conn, "myjob", 1)   # recent
    archive_executions(conn, "myjob", _ts(30))
    remaining = conn.execute(
        "SELECT COUNT(*) FROM executions WHERE job_name='myjob'"
    ).fetchone()[0]
    assert remaining == 1


def test_fetch_archive_returns_moved_rows(conn):
    _insert(conn, "myjob", 40, exit_code=1)
    archive_executions(conn, "myjob", _ts(30))
    rows = fetch_archive(conn, "myjob")
    assert len(rows) == 1
    assert rows[0]["job_name"] == "myjob"
    assert rows[0]["exit_code"] == 1


def test_fetch_archive_contains_archived_at(conn):
    _insert(conn, "myjob", 40)
    archive_executions(conn, "myjob", _ts(30))
    rows = fetch_archive(conn, "myjob")
    assert "archived_at" in rows[0]
    assert rows[0]["archived_at"] is not None


def test_purge_archive_removes_all_rows(conn):
    _insert(conn, "myjob", 40)
    archive_executions(conn, "myjob", _ts(30))
    deleted = purge_archive(conn)
    assert deleted == 1
    assert fetch_archive(conn, "myjob") == []


def test_purge_archive_scoped_to_job(conn):
    _insert(conn, "job-a", 40)
    _insert(conn, "job-b", 40)
    archive_executions(conn, "job-a", _ts(30))
    archive_executions(conn, "job-b", _ts(30))
    purge_archive(conn, job_name="job-a")
    assert fetch_archive(conn, "job-a") == []
    assert len(fetch_archive(conn, "job-b")) == 1
