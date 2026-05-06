"""Tests for crontrace.deduplicator."""

import sqlite3
import pytest

from crontrace.deduplicator import (
    get_last_code,
    set_last_code,
    should_notify,
)

TS = "2024-01-15T10:00:00"
TS2 = "2024-01-15T11:00:00"


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_last_code_returns_none_when_missing(conn):
    assert get_last_code(conn, "my_job") is None


def test_set_and_get_last_code_round_trip(conn):
    set_last_code(conn, "my_job", 0, TS)
    assert get_last_code(conn, "my_job") == 0


def test_set_last_code_overwrites_existing(conn):
    set_last_code(conn, "my_job", 0, TS)
    set_last_code(conn, "my_job", 1, TS2)
    assert get_last_code(conn, "my_job") == 1


def test_set_last_code_independent_per_job(conn):
    set_last_code(conn, "job_a", 0, TS)
    set_last_code(conn, "job_b", 1, TS)
    assert get_last_code(conn, "job_a") == 0
    assert get_last_code(conn, "job_b") == 1


def test_should_notify_true_when_no_prior_record(conn):
    assert should_notify(conn, "new_job", 0) is True


def test_should_notify_false_when_code_unchanged(conn):
    set_last_code(conn, "my_job", 0, TS)
    assert should_notify(conn, "my_job", 0) is False


def test_should_notify_true_when_code_changes_success_to_fail(conn):
    set_last_code(conn, "my_job", 0, TS)
    assert should_notify(conn, "my_job", 1) is True


def test_should_notify_true_when_code_changes_fail_to_success(conn):
    set_last_code(conn, "my_job", 2, TS)
    assert should_notify(conn, "my_job", 0) is True


def test_should_notify_does_not_mutate_state(conn):
    """Calling should_notify must not alter the stored code."""
    set_last_code(conn, "my_job", 0, TS)
    should_notify(conn, "my_job", 1)  # different code — but we don't persist here
    assert get_last_code(conn, "my_job") == 0
