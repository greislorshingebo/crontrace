"""Tests for crontrace.job_snapshots."""

import sqlite3
import pytest

from crontrace.job_snapshots import (
    save_snapshot,
    get_snapshot,
    delete_snapshot,
    list_snapshots,
)

_TS = "2024-01-15T10:00:00"


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


@pytest.fixture()
def conn_with_snapshots(conn):
    """Connection pre-populated with a small set of snapshots for reuse."""
    save_snapshot(conn, "job_a", 0, 1.0, "output_a", _TS)
    save_snapshot(conn, "job_b", 1, 2.5, "output_b", _TS)
    save_snapshot(conn, "job_c", 2, None, None, _TS)
    return conn


def test_get_snapshot_returns_none_when_missing(conn):
    assert get_snapshot(conn, "backup") is None


def test_save_and_get_round_trip(conn):
    save_snapshot(conn, "backup", 0, 12.5, "done", _TS)
    snap = get_snapshot(conn, "backup")
    assert snap is not None
    assert snap["job_name"] == "backup"
    assert snap["exit_code"] == 0
    assert snap["duration"] == pytest.approx(12.5)
    assert snap["stdout"] == "done"
    assert snap["captured_at"] == _TS


def test_save_snapshot_overwrites_existing(conn):
    save_snapshot(conn, "backup", 0, 5.0, "old", _TS)
    save_snapshot(conn, "backup", 1, 7.0, "new", "2024-02-01T00:00:00")
    snap = get_snapshot(conn, "backup")
    assert snap["exit_code"] == 1
    assert snap["stdout"] == "new"
    assert snap["captured_at"] == "2024-02-01T00:00:00"


def test_save_snapshot_independent_per_job(conn):
    save_snapshot(conn, "job_a", 0, 1.0, "a", _TS)
    save_snapshot(conn, "job_b", 2, 2.0, "b", _TS)
    assert get_snapshot(conn, "job_a")["exit_code"] == 0
    assert get_snapshot(conn, "job_b")["exit_code"] == 2


def test_delete_snapshot_returns_true_when_exists(conn):
    save_snapshot(conn, "backup", 0, 1.0, None, _TS)
    assert delete_snapshot(conn, "backup") is True


def test_delete_snapshot_returns_false_when_missing(conn):
    assert delete_snapshot(conn, "nonexistent") is False


def test_delete_removes_record(conn):
    save_snapshot(conn, "backup", 0, 1.0, None, _TS)
    delete_snapshot(conn, "backup")
    assert get_snapshot(conn, "backup") is None


def test_list_snapshots_empty_when_none(conn):
    assert list_snapshots(conn) == []


def test_list_snapshots_returns_all_ordered(conn):
    save_snapshot(conn, "zzz", 0, 1.0, None, _TS)
    save_snapshot(conn, "aaa", 1, 2.0, None, _TS)
    names = [s["job_name"] for s in list_snapshots(conn)]
    assert names == ["aaa", "zzz"]


def test_list_snapshots_count(conn_with_snapshots):
    """list_snapshots returns one entry per saved job."""
    assert len(list_snapshots(conn_with_snapshots)) == 3


def test_list_snapshots_contains_all_fields(conn_with_snapshots):
    """Each entry returned by list_snapshots exposes the expected keys."""
    expected_keys = {"job_name", "exit_code", "duration", "stdout", "captured_at"}
    for snap in list_snapshots(conn_with_snapshots):
        assert expected_keys <= snap.keys()


def test_snapshot_stdout_can_be_none(conn):
    save_snapshot(conn, "silent", 0, 3.0, None, _TS)
    snap = get_snapshot(conn, "silent")
    assert snap["stdout"] is None


def test_snapshot_duration_can_be_none(conn):
    save_snapshot(conn, "nodur", 0, None, None, _TS)
    snap = get_snapshot(conn, "nodur")
    assert snap["duration"] is None
