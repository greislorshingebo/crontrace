"""Tests for crontrace.pruner."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from crontrace.pruner import _cutoff_utc, prune_old_records
from crontrace.storage import get_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(days_ago: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _insert(conn: sqlite3.Connection, job: str, days_ago: float, exit_code: int = 0) -> None:
    conn.execute(
        "INSERT INTO executions (job_name, started_at, duration_s, exit_code)"
        " VALUES (?, ?, ?, ?)",
        (job, _ts(days_ago), 1.0, exit_code),
    )
    conn.commit()


@pytest.fixture()
def tmp_db(tmp_path: Path) -> str:
    db = str(tmp_path / "test.db")
    conn = get_connection(db)
    conn.close()
    return db


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_cutoff_utc_returns_string():
    result = _cutoff_utc(7)
    assert isinstance(result, str)
    assert len(result) == 19  # YYYY-MM-DDTHH:MM:SS


def test_prune_removes_old_records(tmp_db):
    conn = get_connection(tmp_db)
    _insert(conn, "backup", days_ago=10)
    _insert(conn, "backup", days_ago=2)
    conn.close()

    deleted = prune_old_records(tmp_db, days=7)
    assert deleted == 1

    conn = get_connection(tmp_db)
    rows = conn.execute("SELECT * FROM executions").fetchall()
    conn.close()
    assert len(rows) == 1


def test_prune_with_job_name_filter(tmp_db):
    conn = get_connection(tmp_db)
    _insert(conn, "backup", days_ago=10)
    _insert(conn, "report", days_ago=10)
    conn.close()

    deleted = prune_old_records(tmp_db, days=7, job_name="backup")
    assert deleted == 1

    conn = get_connection(tmp_db)
    rows = conn.execute("SELECT job_name FROM executions").fetchall()
    conn.close()
    assert rows[0][0] == "report"


def test_prune_nothing_to_delete(tmp_db):
    conn = get_connection(tmp_db)
    _insert(conn, "backup", days_ago=1)
    conn.close()

    deleted = prune_old_records(tmp_db, days=7)
    assert deleted == 0


def test_prune_invalid_days_raises(tmp_db):
    with pytest.raises(ValueError, match="positive"):
        prune_old_records(tmp_db, days=0)
