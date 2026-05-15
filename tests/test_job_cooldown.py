"""Tests for crontrace.job_cooldown."""

import sqlite3
from datetime import datetime, timezone, timedelta

import pytest

from crontrace.job_cooldown import (
    set_cooldown,
    get_cooldown,
    delete_cooldown,
    list_cooldowns,
    is_in_cooldown,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_cooldown_returns_none_when_missing(conn):
    assert get_cooldown(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_cooldown(conn, "backup", 300, note="5 min gap")
    result = get_cooldown(conn, "backup")
    assert result is not None
    assert result["job_name"] == "backup"
    assert result["seconds"] == 300
    assert result["note"] == "5 min gap"


def test_set_cooldown_note_defaults_to_none(conn):
    set_cooldown(conn, "sync", 60)
    result = get_cooldown(conn, "sync")
    assert result["note"] is None


def test_set_cooldown_overwrites_existing(conn):
    set_cooldown(conn, "backup", 300)
    set_cooldown(conn, "backup", 600, note="updated")
    result = get_cooldown(conn, "backup")
    assert result["seconds"] == 600
    assert result["note"] == "updated"


def test_set_cooldown_independent_per_job(conn):
    set_cooldown(conn, "job_a", 120)
    set_cooldown(conn, "job_b", 240)
    assert get_cooldown(conn, "job_a")["seconds"] == 120
    assert get_cooldown(conn, "job_b")["seconds"] == 240


def test_set_cooldown_negative_seconds_raises(conn):
    with pytest.raises(ValueError):
        set_cooldown(conn, "bad", -1)


def test_delete_cooldown_returns_true_when_exists(conn):
    set_cooldown(conn, "backup", 300)
    assert delete_cooldown(conn, "backup") is True
    assert get_cooldown(conn, "backup") is None


def test_delete_cooldown_returns_false_when_missing(conn):
    assert delete_cooldown(conn, "nonexistent") is False


def test_list_cooldowns_empty_when_none(conn):
    assert list_cooldowns(conn) == []


def test_list_cooldowns_returns_all_ordered(conn):
    set_cooldown(conn, "zzz", 10)
    set_cooldown(conn, "aaa", 20)
    results = list_cooldowns(conn)
    assert len(results) == 2
    assert results[0]["job_name"] == "aaa"
    assert results[1]["job_name"] == "zzz"


def test_is_in_cooldown_false_when_no_record(conn):
    last_run = datetime.now(timezone.utc) - timedelta(seconds=10)
    assert is_in_cooldown(conn, "backup", last_run) is False


def test_is_in_cooldown_false_when_last_run_is_none(conn):
    set_cooldown(conn, "backup", 300)
    assert is_in_cooldown(conn, "backup", None) is False


def test_is_in_cooldown_true_when_within_window(conn):
    set_cooldown(conn, "backup", 300)
    last_run = datetime.now(timezone.utc) - timedelta(seconds=60)
    assert is_in_cooldown(conn, "backup", last_run) is True


def test_is_in_cooldown_false_when_outside_window(conn):
    set_cooldown(conn, "backup", 60)
    last_run = datetime.now(timezone.utc) - timedelta(seconds=120)
    assert is_in_cooldown(conn, "backup", last_run) is False


def test_is_in_cooldown_accepts_naive_datetime(conn):
    set_cooldown(conn, "backup", 300)
    last_run = datetime.utcnow() - timedelta(seconds=30)
    assert is_in_cooldown(conn, "backup", last_run) is True


def test_set_cooldown_strips_whitespace(conn):
    set_cooldown(conn, "  trim_me  ", 100)
    assert get_cooldown(conn, "trim_me") is not None
