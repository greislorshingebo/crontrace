"""Tests for crontrace.job_lock."""

import sqlite3
import pytest

from crontrace.job_lock import (
    acquire_lock,
    release_lock,
    get_lock_info,
    is_locked,
)

NOW = "2024-01-15T10:00:00"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_acquire_lock_returns_true_when_free(conn):
    assert acquire_lock(conn, "backup", 1234, NOW) is True


def test_acquire_lock_returns_false_when_already_locked(conn):
    acquire_lock(conn, "backup", 1234, NOW)
    assert acquire_lock(conn, "backup", 5678, NOW) is False


def test_acquire_different_jobs_independently(conn):
    assert acquire_lock(conn, "job_a", 1, NOW) is True
    assert acquire_lock(conn, "job_b", 2, NOW) is True


def test_is_locked_false_before_acquire(conn):
    assert is_locked(conn, "backup") is False


def test_is_locked_true_after_acquire(conn):
    acquire_lock(conn, "backup", 1234, NOW)
    assert is_locked(conn, "backup") is True


def test_release_lock_removes_entry(conn):
    acquire_lock(conn, "backup", 1234, NOW)
    release_lock(conn, "backup")
    assert is_locked(conn, "backup") is False


def test_release_lock_is_idempotent(conn):
    release_lock(conn, "backup")  # should not raise
    assert is_locked(conn, "backup") is False


def test_get_lock_info_returns_none_when_missing(conn):
    assert get_lock_info(conn, "missing_job") is None


def test_get_lock_info_returns_dict(conn):
    acquire_lock(conn, "backup", 9999, NOW)
    info = get_lock_info(conn, "backup")
    assert info is not None
    assert info["job_name"] == "backup"
    assert info["pid"] == 9999
    assert info["acquired"] == NOW


def test_reacquire_after_release(conn):
    acquire_lock(conn, "backup", 1, NOW)
    release_lock(conn, "backup")
    assert acquire_lock(conn, "backup", 2, NOW) is True
