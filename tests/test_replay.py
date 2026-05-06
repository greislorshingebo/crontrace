"""Tests for crontrace.replay."""

import sqlite3
import tempfile
import os
import pytest

from crontrace.storage import get_connection
from crontrace.replay import fetch_execution, replay_execution


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    conn = get_connection(path)
    conn.execute(
        "INSERT INTO executions (job_name, command, exit_code, started_at, duration_s)"
        " VALUES (?, ?, ?, ?, ?)",
        ("backup", "echo hello", 0, "2024-01-01T00:00:00Z", 1.23),
    )
    conn.commit()
    conn.close()
    return path


def test_fetch_execution_returns_dict(db_path):
    result = fetch_execution(db_path, 1)
    assert result is not None
    assert result["job_name"] == "backup"
    assert result["command"] == "echo hello"
    assert result["exit_code"] == 0


def test_fetch_execution_missing_returns_none(db_path):
    result = fetch_execution(db_path, 9999)
    assert result is None


def test_replay_execution_success(db_path):
    code = replay_execution(db_path, 1, record=True)
    assert code == 0


def test_replay_execution_records_new_row(db_path):
    replay_execution(db_path, 1, record=True)
    conn = get_connection(db_path)
    rows = conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0]
    conn.close()
    assert rows == 2


def test_replay_execution_no_record_does_not_persist(db_path):
    replay_execution(db_path, 1, record=False)
    conn = get_connection(db_path)
    rows = conn.execute("SELECT COUNT(*) FROM executions").fetchone()[0]
    conn.close()
    assert rows == 1


def test_replay_execution_invalid_id_raises(db_path):
    with pytest.raises(ValueError, match="No execution found"):
        replay_execution(db_path, 9999)


def test_replay_execution_failing_command(db_path):
    conn = get_connection(db_path)
    conn.execute(
        "INSERT INTO executions (job_name, command, exit_code, started_at, duration_s)"
        " VALUES (?, ?, ?, ?, ?)",
        ("bad", "exit 42", 42, "2024-01-02T00:00:00Z", 0.1),
    )
    conn.commit()
    conn.close()
    code = replay_execution(db_path, 2, record=False)
    assert code == 42
