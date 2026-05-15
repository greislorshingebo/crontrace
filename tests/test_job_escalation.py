"""Tests for crontrace.job_escalation."""

import sqlite3
import pytest

from crontrace.job_escalation import (
    set_escalation,
    get_escalation,
    delete_escalation,
    list_escalations,
    is_escalated,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_escalation_returns_none_when_missing(conn):
    assert get_escalation(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_escalation(conn, "backup", threshold=3, contact="ops@example.com")
    result = get_escalation(conn, "backup")
    assert result["job_name"] == "backup"
    assert result["threshold"] == 3
    assert result["contact"] == "ops@example.com"
    assert result["enabled"] is True
    assert result["note"] is None


def test_set_escalation_with_note(conn):
    set_escalation(conn, "cleanup", threshold=5, note="page on-call")
    result = get_escalation(conn, "cleanup")
    assert result["note"] == "page on-call"


def test_set_escalation_disabled(conn):
    set_escalation(conn, "report", threshold=2, enabled=False)
    result = get_escalation(conn, "report")
    assert result["enabled"] is False


def test_set_escalation_overwrites_existing(conn):
    set_escalation(conn, "sync", threshold=2)
    set_escalation(conn, "sync", threshold=10, contact="team@example.com")
    result = get_escalation(conn, "sync")
    assert result["threshold"] == 10
    assert result["contact"] == "team@example.com"


def test_set_escalation_independent_per_job(conn):
    set_escalation(conn, "job_a", threshold=1)
    set_escalation(conn, "job_b", threshold=9)
    assert get_escalation(conn, "job_a")["threshold"] == 1
    assert get_escalation(conn, "job_b")["threshold"] == 9


def test_threshold_below_one_raises(conn):
    with pytest.raises(ValueError, match="threshold"):
        set_escalation(conn, "bad", threshold=0)


def test_delete_escalation_returns_true_when_exists(conn):
    set_escalation(conn, "nightly", threshold=3)
    assert delete_escalation(conn, "nightly") is True
    assert get_escalation(conn, "nightly") is None


def test_delete_escalation_returns_false_when_missing(conn):
    assert delete_escalation(conn, "ghost") is False


def test_list_escalations_empty(conn):
    assert list_escalations(conn) == []


def test_list_escalations_returns_all(conn):
    set_escalation(conn, "alpha", threshold=2)
    set_escalation(conn, "beta", threshold=4)
    results = list_escalations(conn)
    names = [r["job_name"] for r in results]
    assert "alpha" in names
    assert "beta" in names


def test_list_escalations_ordered_by_job_name(conn):
    set_escalation(conn, "zzz", threshold=1)
    set_escalation(conn, "aaa", threshold=1)
    results = list_escalations(conn)
    assert results[0]["job_name"] == "aaa"
    assert results[-1]["job_name"] == "zzz"


def test_is_escalated_returns_false_when_no_policy(conn):
    assert is_escalated(conn, "unknown", 10) is False


def test_is_escalated_true_when_threshold_met(conn):
    set_escalation(conn, "critical", threshold=3)
    assert is_escalated(conn, "critical", 3) is True
    assert is_escalated(conn, "critical", 5) is True


def test_is_escalated_false_when_below_threshold(conn):
    set_escalation(conn, "critical", threshold=3)
    assert is_escalated(conn, "critical", 2) is False


def test_is_escalated_false_when_disabled(conn):
    set_escalation(conn, "quiet", threshold=1, enabled=False)
    assert is_escalated(conn, "quiet", 99) is False
