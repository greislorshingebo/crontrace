"""Tests for crontrace.job_pinning."""

import sqlite3
import pytest

from crontrace.job_pinning import (
    pin_execution,
    get_pin,
    unpin,
    list_pins,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_pin_returns_none_when_missing(conn):
    assert get_pin(conn, "backup") is None


def test_pin_and_get_round_trip(conn):
    pin_execution(conn, "backup", 42, note="golden run", pinned_at="2024-01-01T00:00:00")
    result = get_pin(conn, "backup")
    assert result is not None
    assert result["job_name"] == "backup"
    assert result["run_id"] == 42
    assert result["note"] == "golden run"
    assert result["pinned_at"] == "2024-01-01T00:00:00"


def test_pin_overwrites_existing(conn):
    pin_execution(conn, "backup", 1, pinned_at="2024-01-01T00:00:00")
    pin_execution(conn, "backup", 99, note="updated", pinned_at="2024-06-01T00:00:00")
    result = get_pin(conn, "backup")
    assert result["run_id"] == 99
    assert result["note"] == "updated"


def test_pin_note_defaults_to_none(conn):
    pin_execution(conn, "sync", 7, pinned_at="2024-01-01T00:00:00")
    result = get_pin(conn, "sync")
    assert result["note"] is None


def test_unpin_returns_true_when_existed(conn):
    pin_execution(conn, "deploy", 5, pinned_at="2024-01-01T00:00:00")
    assert unpin(conn, "deploy") is True


def test_unpin_returns_false_when_missing(conn):
    assert unpin(conn, "nonexistent") is False


def test_unpin_removes_record(conn):
    pin_execution(conn, "report", 3, pinned_at="2024-01-01T00:00:00")
    unpin(conn, "report")
    assert get_pin(conn, "report") is None


def test_list_pins_empty_returns_empty_list(conn):
    assert list_pins(conn) == []


def test_list_pins_returns_all_entries(conn):
    pin_execution(conn, "alpha", 1, pinned_at="2024-01-01T00:00:00")
    pin_execution(conn, "beta", 2, pinned_at="2024-01-02T00:00:00")
    results = list_pins(conn)
    assert len(results) == 2


def test_list_pins_ordered_by_job_name(conn):
    pin_execution(conn, "zzz", 9, pinned_at="2024-01-01T00:00:00")
    pin_execution(conn, "aaa", 1, pinned_at="2024-01-01T00:00:00")
    names = [r["job_name"] for r in list_pins(conn)]
    assert names == sorted(names)


def test_pin_independent_per_job(conn):
    pin_execution(conn, "job_a", 10, pinned_at="2024-01-01T00:00:00")
    pin_execution(conn, "job_b", 20, pinned_at="2024-01-01T00:00:00")
    assert get_pin(conn, "job_a")["run_id"] == 10
    assert get_pin(conn, "job_b")["run_id"] == 20
