"""Tests for crontrace.job_history."""

import sqlite3
import pytest

from crontrace.storage import get_connection, insert_execution
from crontrace.job_history import (
    fetch_job_history,
    last_success,
    last_failure,
    streak,
    render_job_history,
)


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "test.db"
    c = get_connection(str(db))
    yield c
    c.close()


def _insert(conn, job, started_at, duration, exit_code):
    insert_execution(conn, job, started_at, duration, exit_code, "")


def test_fetch_job_history_returns_only_matching_job(conn):
    _insert(conn, "job_a", "2024-01-01T00:00:00", 1.0, 0)
    _insert(conn, "job_b", "2024-01-01T00:01:00", 2.0, 1)
    _insert(conn, "job_a", "2024-01-01T00:02:00", 1.5, 0)

    history = fetch_job_history(conn, "job_a")
    assert all(h["job_name"] == "job_a" for h in history)
    assert len(history) == 2


def test_fetch_job_history_empty_when_no_match(conn):
    _insert(conn, "job_a", "2024-01-01T00:00:00", 1.0, 0)
    history = fetch_job_history(conn, "job_z")
    assert history == []


def test_last_success_returns_first_ok(conn):
    rows = [
        {"job_name": "j", "started_at": "2024-01-03", "exit_code": 1, "duration": 1.0},
        {"job_name": "j", "started_at": "2024-01-02", "exit_code": 0, "duration": 2.0},
        {"job_name": "j", "started_at": "2024-01-01", "exit_code": 0, "duration": 1.5},
    ]
    result = last_success(rows)
    assert result is not None
    assert result["started_at"] == "2024-01-02"


def test_last_success_returns_none_when_all_fail():
    rows = [
        {"exit_code": 1, "started_at": "2024-01-01", "duration": 1.0},
        {"exit_code": 2, "started_at": "2024-01-02", "duration": 1.0},
    ]
    assert last_success(rows) is None


def test_last_failure_returns_first_nonzero():
    rows = [
        {"exit_code": 0, "started_at": "2024-01-03", "duration": 1.0},
        {"exit_code": 1, "started_at": "2024-01-02", "duration": 1.0},
    ]
    result = last_failure(rows)
    assert result is not None
    assert result["started_at"] == "2024-01-02"


def test_streak_empty_returns_none_type():
    assert streak([]) == {"type": "none", "length": 0}


def test_streak_all_ok():
    rows = [{"exit_code": 0}] * 4
    result = streak(rows)
    assert result == {"type": "ok", "length": 4}


def test_streak_mixed_stops_at_first_break():
    rows = [
        {"exit_code": 1},
        {"exit_code": 1},
        {"exit_code": 0},
    ]
    result = streak(rows)
    assert result == {"type": "fail", "length": 2}


def test_render_job_history_no_history():
    output = render_job_history("myjob", [])
    assert "No history" in output
    assert "myjob" in output


def test_render_job_history_contains_job_name_and_status():
    rows = [
        {"job_name": "myjob", "started_at": "2024-06-01T12:00:00",
         "exit_code": 0, "duration": 3.5},
        {"job_name": "myjob", "started_at": "2024-06-01T11:00:00",
         "exit_code": 1, "duration": 1.2},
    ]
    output = render_job_history("myjob", rows)
    assert "myjob" in output
    assert "OK" in output
    assert "FAIL" in output
    assert "Last success" in output
    assert "Last failure" in output
