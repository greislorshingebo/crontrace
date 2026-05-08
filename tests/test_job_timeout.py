"""Tests for crontrace.job_timeout and crontrace.timeout_reporter."""

import sqlite3
import pytest

from crontrace.job_timeout import (
    set_timeout,
    get_timeout,
    delete_timeout,
    list_timeouts,
    is_timed_out,
)
from crontrace.timeout_reporter import (
    render_timeout_row,
    render_timeout_table,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# --- job_timeout ---

def test_get_timeout_returns_none_when_missing(conn):
    assert get_timeout(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_timeout(conn, "backup", 120)
    assert get_timeout(conn, "backup") == 120


def test_set_timeout_overwrites_existing(conn):
    set_timeout(conn, "backup", 60)
    set_timeout(conn, "backup", 300)
    assert get_timeout(conn, "backup") == 300


def test_set_timeout_independent_per_job(conn):
    set_timeout(conn, "job_a", 30)
    set_timeout(conn, "job_b", 90)
    assert get_timeout(conn, "job_a") == 30
    assert get_timeout(conn, "job_b") == 90


def test_set_timeout_raises_on_zero(conn):
    with pytest.raises(ValueError):
        set_timeout(conn, "backup", 0)


def test_set_timeout_raises_on_negative(conn):
    with pytest.raises(ValueError):
        set_timeout(conn, "backup", -5)


def test_delete_timeout_returns_true_when_exists(conn):
    set_timeout(conn, "backup", 60)
    assert delete_timeout(conn, "backup") is True
    assert get_timeout(conn, "backup") is None


def test_delete_timeout_returns_false_when_missing(conn):
    assert delete_timeout(conn, "nonexistent") is False


def test_list_timeouts_empty(conn):
    assert list_timeouts(conn) == []


def test_list_timeouts_returns_all(conn):
    set_timeout(conn, "alpha", 10)
    set_timeout(conn, "beta", 20)
    rows = list_timeouts(conn)
    names = [r["job_name"] for r in rows]
    assert "alpha" in names and "beta" in names


def test_list_timeouts_contains_expected_keys(conn):
    set_timeout(conn, "myjob", 45)
    row = list_timeouts(conn)[0]
    assert "job_name" in row and "timeout_s" in row and "updated_at" in row


def test_is_timed_out_false_when_no_limit(conn):
    assert is_timed_out(9999.0, "backup", conn) is False


def test_is_timed_out_false_within_limit(conn):
    set_timeout(conn, "backup", 60)
    assert is_timed_out(59.9, "backup", conn) is False


def test_is_timed_out_true_when_exceeded(conn):
    set_timeout(conn, "backup", 60)
    assert is_timed_out(60.1, "backup", conn) is True


# --- timeout_reporter ---

def test_render_row_contains_job_name():
    entry = {"job_name": "nightly", "timeout_s": 120, "updated_at": "2024-01-01T00:00:00Z"}
    assert "nightly" in render_timeout_row(entry)


def test_render_row_contains_timeout():
    entry = {"job_name": "nightly", "timeout_s": 300, "updated_at": "2024-01-01T00:00:00Z"}
    assert "300" in render_timeout_row(entry)


def test_render_table_empty_shows_message():
    assert "No timeout" in render_timeout_table([])


def test_render_table_contains_header():
    entries = [{"job_name": "j", "timeout_s": 10, "updated_at": "2024-01-01T00:00:00Z"}]
    table = render_timeout_table(entries)
    assert "JOB" in table and "TIMEOUT" in table


def test_render_table_contains_all_entries():
    entries = [
        {"job_name": "alpha", "timeout_s": 10, "updated_at": ""},
        {"job_name": "beta", "timeout_s": 20, "updated_at": ""},
    ]
    table = render_timeout_table(entries)
    assert "alpha" in table and "beta" in table
