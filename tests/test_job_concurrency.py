"""Tests for crontrace.job_concurrency."""

import sqlite3
import pytest

from crontrace.job_concurrency import (
    set_concurrency,
    get_concurrency,
    delete_concurrency,
    list_concurrency,
    would_exceed,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_concurrency_returns_none_when_missing(conn):
    assert get_concurrency(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_concurrency(conn, "backup", 3)
    result = get_concurrency(conn, "backup")
    assert result is not None
    assert result["job_name"] == "backup"
    assert result["max_concurrent"] == 3


def test_set_concurrency_overwrites_existing(conn):
    set_concurrency(conn, "backup", 2)
    set_concurrency(conn, "backup", 5)
    assert get_concurrency(conn, "backup")["max_concurrent"] == 5


def test_set_concurrency_independent_per_job(conn):
    set_concurrency(conn, "job_a", 1)
    set_concurrency(conn, "job_b", 4)
    assert get_concurrency(conn, "job_a")["max_concurrent"] == 1
    assert get_concurrency(conn, "job_b")["max_concurrent"] == 4


def test_set_concurrency_rejects_zero(conn):
    with pytest.raises(ValueError):
        set_concurrency(conn, "backup", 0)


def test_set_concurrency_rejects_negative(conn):
    with pytest.raises(ValueError):
        set_concurrency(conn, "backup", -1)


def test_delete_concurrency_returns_true_when_exists(conn):
    set_concurrency(conn, "backup", 2)
    assert delete_concurrency(conn, "backup") is True


def test_delete_concurrency_returns_false_when_missing(conn):
    assert delete_concurrency(conn, "nonexistent") is False


def test_delete_concurrency_removes_entry(conn):
    set_concurrency(conn, "backup", 2)
    delete_concurrency(conn, "backup")
    assert get_concurrency(conn, "backup") is None


def test_list_concurrency_empty_returns_empty_list(conn):
    assert list_concurrency(conn) == []


def test_list_concurrency_returns_all_entries(conn):
    set_concurrency(conn, "job_a", 1)
    set_concurrency(conn, "job_b", 3)
    entries = list_concurrency(conn)
    assert len(entries) == 2
    names = [e["job_name"] for e in entries]
    assert "job_a" in names
    assert "job_b" in names


def test_list_concurrency_ordered_by_name(conn):
    set_concurrency(conn, "zebra", 1)
    set_concurrency(conn, "alpha", 2)
    names = [e["job_name"] for e in list_concurrency(conn)]
    assert names == sorted(names)


def test_would_exceed_false_when_no_limit_configured(conn):
    assert would_exceed(conn, "backup", 99) is False


def test_would_exceed_false_when_under_limit(conn):
    set_concurrency(conn, "backup", 3)
    assert would_exceed(conn, "backup", 2) is False


def test_would_exceed_true_when_at_limit(conn):
    set_concurrency(conn, "backup", 2)
    assert would_exceed(conn, "backup", 2) is True


def test_would_exceed_true_when_over_limit(conn):
    set_concurrency(conn, "backup", 1)
    assert would_exceed(conn, "backup", 5) is True
