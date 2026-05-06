"""Integration tests for the runner + storage layer."""

import sys
import tempfile
from pathlib import Path

import pytest

from crontrace.runner import run_job
from crontrace.storage import get_connection, fetch_recent


@pytest.fixture()
def tmp_db(tmp_path):
    """Return a path to a temporary database file."""
    return tmp_path / "test_history.db"


def test_successful_command_returns_zero(tmp_db):
    code = run_job(f"{sys.executable} -c 'print(1)'", job_name="test-ok", db_path=tmp_db)
    assert code == 0


def test_failed_command_returns_nonzero(tmp_db):
    code = run_job(f"{sys.executable} -c 'raise SystemExit(2)'", job_name="test-fail", db_path=tmp_db)
    assert code == 2


def test_record_is_persisted(tmp_db):
    run_job(f"{sys.executable} -c 'pass'", job_name="persist-test", db_path=tmp_db)
    conn = get_connection(tmp_db)
    rows = fetch_recent(conn, job_name="persist-test")
    conn.close()
    assert len(rows) == 1
    row = rows[0]
    assert row["job_name"] == "persist-test"
    assert row["exit_code"] == 0
    assert row["duration_s"] >= 0


def test_multiple_runs_accumulate(tmp_db):
    for _ in range(3):
        run_job(f"{sys.executable} -c 'pass'", job_name="multi", db_path=tmp_db)
    conn = get_connection(tmp_db)
    rows = fetch_recent(conn, job_name="multi", limit=10)
    conn.close()
    assert len(rows) == 3


def test_unknown_command_returns_127(tmp_db):
    code = run_job("__no_such_binary__", job_name="missing", db_path=tmp_db)
    assert code == 127


def test_fetch_recent_no_filter_returns_all(tmp_db):
    run_job(f"{sys.executable} -c 'pass'", job_name="alpha", db_path=tmp_db)
    run_job(f"{sys.executable} -c 'pass'", job_name="beta", db_path=tmp_db)
    conn = get_connection(tmp_db)
    rows = fetch_recent(conn)
    conn.close()
    job_names = {r["job_name"] for r in rows}
    assert {"alpha", "beta"}.issubset(job_names)
