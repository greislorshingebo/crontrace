"""Tests for crontrace.job_ratelimit."""

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from crontrace.job_ratelimit import (
    delete_ratelimit,
    get_ratelimit,
    is_rate_limited,
    list_ratelimits,
    set_ratelimit,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    # Minimal executions table required by is_rate_limited
    c.execute(
        """
        CREATE TABLE executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            started_at TEXT,
            exit_code INTEGER,
            duration_s REAL
        )
        """
    )
    c.commit()
    yield c
    c.close()


def _insert_exec(conn, job_name, started_at):
    conn.execute(
        "INSERT INTO executions (job_name, started_at, exit_code, duration_s) VALUES (?, ?, 0, 1.0)",
        (job_name, started_at),
    )
    conn.commit()


def _ts(offset_seconds=0):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


# --- set / get ---

def test_get_ratelimit_returns_none_when_missing(conn):
    assert get_ratelimit(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_ratelimit(conn, "backup", max_runs=5, window_seconds=3600)
    rule = get_ratelimit(conn, "backup")
    assert rule["job_name"] == "backup"
    assert rule["max_runs"] == 5
    assert rule["window_s"] == 3600


def test_set_ratelimit_overwrites_existing(conn):
    set_ratelimit(conn, "backup", max_runs=5, window_seconds=3600)
    set_ratelimit(conn, "backup", max_runs=10, window_seconds=7200)
    rule = get_ratelimit(conn, "backup")
    assert rule["max_runs"] == 10
    assert rule["window_s"] == 7200


def test_set_ratelimit_invalid_max_runs_raises(conn):
    with pytest.raises(ValueError, match="max_runs"):
        set_ratelimit(conn, "backup", max_runs=0, window_seconds=60)


def test_set_ratelimit_invalid_window_raises(conn):
    with pytest.raises(ValueError, match="window_seconds"):
        set_ratelimit(conn, "backup", max_runs=3, window_seconds=0)


# --- delete ---

def test_delete_ratelimit_returns_true_when_exists(conn):
    set_ratelimit(conn, "backup", max_runs=3, window_seconds=60)
    assert delete_ratelimit(conn, "backup") is True
    assert get_ratelimit(conn, "backup") is None


def test_delete_ratelimit_returns_false_when_missing(conn):
    assert delete_ratelimit(conn, "nonexistent") is False


# --- list ---

def test_list_ratelimits_empty_returns_empty_list(conn):
    assert list_ratelimits(conn) == []


def test_list_ratelimits_returns_all_entries(conn):
    set_ratelimit(conn, "alpha", max_runs=2, window_seconds=120)
    set_ratelimit(conn, "beta", max_runs=10, window_seconds=3600)
    rules = list_ratelimits(conn)
    assert len(rules) == 2
    assert rules[0]["job_name"] == "alpha"
    assert rules[1]["job_name"] == "beta"


# --- is_rate_limited ---

def test_is_rate_limited_no_rule_returns_false(conn):
    _insert_exec(conn, "backup", _ts())
    assert is_rate_limited(conn, "backup") is False


def test_is_rate_limited_under_limit_returns_false(conn):
    set_ratelimit(conn, "backup", max_runs=3, window_seconds=3600)
    _insert_exec(conn, "backup", _ts(-10))
    _insert_exec(conn, "backup", _ts(-5))
    assert is_rate_limited(conn, "backup") is False


def test_is_rate_limited_at_limit_returns_true(conn):
    set_ratelimit(conn, "backup", max_runs=2, window_seconds=3600)
    _insert_exec(conn, "backup", _ts(-10))
    _insert_exec(conn, "backup", _ts(-5))
    assert is_rate_limited(conn, "backup") is True


def test_is_rate_limited_old_runs_outside_window_not_counted(conn):
    set_ratelimit(conn, "backup", max_runs=2, window_seconds=60)
    # These runs are outside the 60-second window
    _insert_exec(conn, "backup", _ts(-120))
    _insert_exec(conn, "backup", _ts(-90))
    assert is_rate_limited(conn, "backup") is False


def test_is_rate_limited_independent_per_job(conn):
    set_ratelimit(conn, "alpha", max_runs=1, window_seconds=3600)
    _insert_exec(conn, "alpha", _ts(-5))
    _insert_exec(conn, "beta", _ts(-5))
    assert is_rate_limited(conn, "alpha") is True
    assert is_rate_limited(conn, "beta") is False
