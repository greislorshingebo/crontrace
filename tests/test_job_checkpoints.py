"""Tests for crontrace.job_checkpoints."""

import sqlite3
import pytest
from crontrace.job_checkpoints import (
    record_checkpoint,
    get_checkpoints,
    delete_checkpoint,
    checkpoints_for_job,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_checkpoints_empty_when_none(conn):
    result = get_checkpoints(conn, "backup", "run-001")
    assert result == []


def test_record_checkpoint_returns_rowid(conn):
    rowid = record_checkpoint(conn, "backup", "run-001", "start")
    assert isinstance(rowid, int)
    assert rowid > 0


def test_get_checkpoints_returns_added_entry(conn):
    record_checkpoint(conn, "backup", "run-001", "start", note="beginning")
    rows = get_checkpoints(conn, "backup", "run-001")
    assert len(rows) == 1
    assert rows[0]["name"] == "start"
    assert rows[0]["note"] == "beginning"
    assert rows[0]["job_name"] == "backup"
    assert rows[0]["run_id"] == "run-001"


def test_get_checkpoints_multiple_ordered_oldest_first(conn):
    record_checkpoint(conn, "backup", "run-001", "start")
    record_checkpoint(conn, "backup", "run-001", "middle")
    record_checkpoint(conn, "backup", "run-001", "end")
    rows = get_checkpoints(conn, "backup", "run-001")
    names = [r["name"] for r in rows]
    assert names == ["start", "middle", "end"]


def test_get_checkpoints_isolated_by_run_id(conn):
    record_checkpoint(conn, "backup", "run-001", "start")
    record_checkpoint(conn, "backup", "run-002", "start")
    rows = get_checkpoints(conn, "backup", "run-001")
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-001"


def test_delete_checkpoint_returns_true_when_exists(conn):
    rowid = record_checkpoint(conn, "backup", "run-001", "start")
    result = delete_checkpoint(conn, rowid)
    assert result is True
    assert get_checkpoints(conn, "backup", "run-001") == []


def test_delete_checkpoint_returns_false_when_missing(conn):
    result = delete_checkpoint(conn, 9999)
    assert result is False


def test_checkpoints_for_job_returns_all_runs(conn):
    record_checkpoint(conn, "backup", "run-001", "start")
    record_checkpoint(conn, "backup", "run-002", "start")
    record_checkpoint(conn, "other", "run-001", "start")
    rows = checkpoints_for_job(conn, "backup")
    assert len(rows) == 2
    assert all(r["job_name"] == "backup" for r in rows)


def test_checkpoints_for_job_empty_when_none(conn):
    assert checkpoints_for_job(conn, "nonexistent") == []


def test_reached_at_is_utc_string(conn):
    record_checkpoint(conn, "backup", "run-001", "start")
    rows = get_checkpoints(conn, "backup", "run-001")
    ts = rows[0]["reached_at"]
    assert "T" in ts
    assert ts.endswith("Z")
