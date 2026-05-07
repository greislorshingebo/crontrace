"""Tests for crontrace.job_throttle."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from crontrace.job_throttle import (
    clear_throttle,
    get_last_run,
    is_throttled,
    record_run,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# get_last_run
# ---------------------------------------------------------------------------

def test_get_last_run_returns_none_when_missing(conn):
    assert get_last_run(conn, "backup") is None


def test_get_last_run_returns_timestamp_after_record(conn):
    record_run(conn, "backup")
    result = get_last_run(conn, "backup")
    assert result is not None
    # Should be parseable as ISO-8601
    dt = datetime.fromisoformat(result)
    assert dt.tzinfo is not None


# ---------------------------------------------------------------------------
# record_run
# ---------------------------------------------------------------------------

def test_record_run_overwrites_previous(conn):
    record_run(conn, "sync")
    first = get_last_run(conn, "sync")
    # Small sleep so timestamps differ
    time.sleep(0.05)
    record_run(conn, "sync")
    second = get_last_run(conn, "sync")
    assert second != first
    assert second > first  # type: ignore[operator]


def test_record_run_independent_per_job(conn):
    record_run(conn, "job_a")
    assert get_last_run(conn, "job_b") is None


# ---------------------------------------------------------------------------
# is_throttled
# ---------------------------------------------------------------------------

def test_is_throttled_false_when_no_record(conn):
    assert is_throttled(conn, "cleanup", min_interval_seconds=60) is False


def test_is_throttled_true_when_ran_recently(conn):
    record_run(conn, "cleanup")
    assert is_throttled(conn, "cleanup", min_interval_seconds=3600) is True


def test_is_throttled_false_when_interval_passed(conn):
    # Simulate a last_run that is well in the past
    past = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    conn.execute(
        "INSERT INTO job_throttle (job_name, last_run) VALUES (?, ?)",
        ("oldrun", past),
    )
    conn.commit()
    assert is_throttled(conn, "oldrun", min_interval_seconds=60) is False


def test_is_throttled_boundary_exact_interval(conn):
    # Exactly at the boundary should NOT be throttled (elapsed == interval)
    past = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    conn.execute(
        "INSERT INTO job_throttle (job_name, last_run) VALUES (?, ?)",
        ("boundary", past),
    )
    conn.commit()
    assert is_throttled(conn, "boundary", min_interval_seconds=60) is False


# ---------------------------------------------------------------------------
# clear_throttle
# ---------------------------------------------------------------------------

def test_clear_throttle_removes_record(conn):
    record_run(conn, "purge")
    clear_throttle(conn, "purge")
    assert get_last_run(conn, "purge") is None


def test_clear_throttle_noop_when_missing(conn):
    # Should not raise
    clear_throttle(conn, "nonexistent")
    assert get_last_run(conn, "nonexistent") is None
