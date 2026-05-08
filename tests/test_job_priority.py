"""Tests for crontrace.job_priority."""

import sqlite3
import pytest

from crontrace.job_priority import (
    DEFAULT_PRIORITY,
    VALID_PRIORITIES,
    delete_priority,
    get_priority,
    list_priorities,
    set_priority,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_priority_returns_default_when_missing(conn):
    assert get_priority(conn, "unknown-job") == DEFAULT_PRIORITY


def test_set_and_get_round_trip(conn):
    set_priority(conn, "my-job", "high")
    assert get_priority(conn, "my-job") == "high"


def test_set_priority_overwrites_existing(conn):
    set_priority(conn, "my-job", "low")
    set_priority(conn, "my-job", "critical")
    assert get_priority(conn, "my-job") == "critical"


def test_set_priority_independent_per_job(conn):
    set_priority(conn, "job-a", "high")
    set_priority(conn, "job-b", "low")
    assert get_priority(conn, "job-a") == "high"
    assert get_priority(conn, "job-b") == "low"


def test_invalid_priority_raises_value_error(conn):
    with pytest.raises(ValueError, match="Invalid priority"):
        set_priority(conn, "my-job", "ultra")


def test_all_valid_priorities_accepted(conn):
    for pri in VALID_PRIORITIES:
        set_priority(conn, f"job-{pri}", pri)
        assert get_priority(conn, f"job-{pri}") == pri


def test_delete_priority_returns_true_when_present(conn):
    set_priority(conn, "my-job", "high")
    assert delete_priority(conn, "my-job") is True


def test_delete_priority_returns_false_when_missing(conn):
    assert delete_priority(conn, "ghost-job") is False


def test_delete_priority_resets_to_default(conn):
    set_priority(conn, "my-job", "critical")
    delete_priority(conn, "my-job")
    assert get_priority(conn, "my-job") == DEFAULT_PRIORITY


def test_list_priorities_empty_returns_empty_list(conn):
    assert list_priorities(conn) == []


def test_list_priorities_contains_set_jobs(conn):
    set_priority(conn, "job-a", "high")
    set_priority(conn, "job-b", "low")
    rows = list_priorities(conn)
    names = [r["job_name"] for r in rows]
    assert "job-a" in names
    assert "job-b" in names


def test_list_priorities_ordered_highest_first(conn):
    set_priority(conn, "job-low", "low")
    set_priority(conn, "job-critical", "critical")
    set_priority(conn, "job-normal", "normal")
    rows = list_priorities(conn)
    priorities = [r["priority"] for r in rows]
    assert priorities.index("critical") < priorities.index("normal")
    assert priorities.index("normal") < priorities.index("low")


def test_list_priorities_row_has_expected_keys(conn):
    set_priority(conn, "my-job", "high")
    row = list_priorities(conn)[0]
    assert "job_name" in row
    assert "priority" in row
    assert "updated_at" in row
