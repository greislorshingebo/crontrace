"""Tests for crontrace.schedule_runner."""

from __future__ import annotations

import datetime
import sqlite3
import os
import pytest

from crontrace.schedule_store import upsert_schedule, _ensure_table
from crontrace.storage import get_connection
from crontrace.schedule_runner import find_due_jobs, run_due_jobs


@pytest.fixture()
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    # Initialise both tables
    conn = get_connection(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS executions "
        "(id INTEGER PRIMARY KEY, job_name TEXT, started_at TEXT, "
        "duration_s REAL, exit_code INTEGER, output TEXT)"
    )
    conn.commit()
    conn.close()
    _ensure_table(path)
    return path


# ---------------------------------------------------------------------------
# find_due_jobs
# ---------------------------------------------------------------------------

def test_find_due_jobs_empty_db_returns_empty(db_path):
    result = find_due_jobs(db_path)
    assert result == []


def test_find_due_jobs_returns_due_job(db_path):
    # Every-minute schedule is always due
    upsert_schedule(db_path, "heartbeat", "* * * * *", "echo heartbeat")
    result = find_due_jobs(db_path)
    assert "heartbeat" in result


def test_find_due_jobs_skips_future_job(db_path):
    # Use a fixed past moment so we can craft a schedule that won't fire
    # A schedule for the 59th minute will not be due at minute 0.
    now = datetime.datetime(2024, 1, 1, 12, 0, 0)  # minute == 0
    upsert_schedule(db_path, "rare_job", "59 23 31 12 *", "echo rare")
    result = find_due_jobs(db_path, now=now)
    assert "rare_job" not in result


def test_find_due_jobs_multiple_jobs(db_path):
    upsert_schedule(db_path, "job_a", "* * * * *", "echo a")
    upsert_schedule(db_path, "job_b", "* * * * *", "echo b")
    result = find_due_jobs(db_path)
    assert "job_a" in result
    assert "job_b" in result


# ---------------------------------------------------------------------------
# run_due_jobs
# ---------------------------------------------------------------------------

def test_run_due_jobs_empty_returns_empty(db_path):
    results = run_due_jobs(db_path)
    assert results == []


def test_run_due_jobs_executes_and_returns_exit_code(db_path):
    upsert_schedule(db_path, "say_hi", "* * * * *", "echo hi")
    results = run_due_jobs(db_path)
    assert len(results) == 1
    job_name, exit_code = results[0]
    assert job_name == "say_hi"
    assert exit_code == 0


def test_run_due_jobs_failing_command_nonzero(db_path):
    upsert_schedule(db_path, "bad_job", "* * * * *", "exit 2")
    results = run_due_jobs(db_path)
    assert any(name == "bad_job" and code != 0 for name, code in results)


def test_run_due_jobs_records_persisted(db_path):
    upsert_schedule(db_path, "recorder", "* * * * *", "echo stored")
    run_due_jobs(db_path)
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT job_name FROM executions WHERE job_name='recorder'"
    ).fetchall()
    conn.close()
    assert len(rows) >= 1
