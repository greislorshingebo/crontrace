"""Tests for crontrace.job_quota."""

import sqlite3
from datetime import datetime, timezone

import pytest

from crontrace.job_quota import (
    set_quota,
    get_quota,
    delete_quota,
    list_quotas,
    is_quota_exceeded,
    _window_start,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def _make_executions(c: sqlite3.Connection, job: str, timestamps: list):
    c.execute(
        "CREATE TABLE IF NOT EXISTS executions "
        "(job_name TEXT, started_at TEXT, exit_code INTEGER, duration_s REAL)"
    )
    for ts in timestamps:
        c.execute(
            "INSERT INTO executions VALUES (?, ?, 0, 1.0)",
            (job, ts),
        )
    c.commit()


def test_get_quota_returns_none_when_missing(conn):
    assert get_quota(conn, "myjob") is None


def test_set_and_get_round_trip(conn):
    set_quota(conn, "backup", 5, "day")
    q = get_quota(conn, "backup")
    assert q["job_name"] == "backup"
    assert q["max_runs"] == 5
    assert q["window"] == "day"


def test_set_quota_overwrites_existing(conn):
    set_quota(conn, "backup", 5, "day")
    set_quota(conn, "backup", 10, "week")
    q = get_quota(conn, "backup")
    assert q["max_runs"] == 10
    assert q["window"] == "week"


def test_set_quota_invalid_window_raises(conn):
    with pytest.raises(ValueError, match="window"):
        set_quota(conn, "job", 3, "month")


def test_set_quota_zero_max_runs_raises(conn):
    with pytest.raises(ValueError, match="max_runs"):
        set_quota(conn, "job", 0, "hour")


def test_delete_quota_returns_true_when_exists(conn):
    set_quota(conn, "job", 2, "hour")
    assert delete_quota(conn, "job") is True
    assert get_quota(conn, "job") is None


def test_delete_quota_returns_false_when_missing(conn):
    assert delete_quota(conn, "ghost") is False


def test_list_quotas_empty_returns_empty_list(conn):
    assert list_quotas(conn) == []


def test_list_quotas_returns_all_entries(conn):
    set_quota(conn, "alpha", 3, "day")
    set_quota(conn, "beta", 1, "hour")
    result = list_quotas(conn)
    names = [r["job_name"] for r in result]
    assert "alpha" in names
    assert "beta" in names


def test_window_start_hour():
    now = datetime(2024, 6, 15, 14, 37, 22, tzinfo=timezone.utc)
    assert _window_start("hour", now) == "2024-06-15T14:00:00Z"


def test_window_start_day():
    now = datetime(2024, 6, 15, 14, 37, 22, tzinfo=timezone.utc)
    assert _window_start("day", now) == "2024-06-15T00:00:00Z"


def test_is_quota_exceeded_no_quota_returns_false(conn):
    assert is_quota_exceeded(conn, "anyjob") is False


def test_is_quota_exceeded_under_limit_returns_false(conn):
    set_quota(conn, "sync", 5, "day")
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _make_executions(conn, "sync", [ts, ts])
    assert is_quota_exceeded(conn, "sync") is False


def test_is_quota_exceeded_at_limit_returns_true(conn):
    set_quota(conn, "sync", 2, "day")
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    _make_executions(conn, "sync", [ts, ts])
    assert is_quota_exceeded(conn, "sync") is True


def test_is_quota_exceeded_no_executions_table_returns_false(conn):
    set_quota(conn, "job", 1, "hour")
    # executions table does not exist — should not raise
    assert is_quota_exceeded(conn, "job") is False
