"""Tests for crontrace.job_blackout."""

import sqlite3
from datetime import datetime

import pytest

from crontrace.job_blackout import (
    delete_blackout,
    get_blackout,
    is_blacked_out,
    list_blackouts,
    set_blackout,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# get_blackout
# ---------------------------------------------------------------------------

def test_get_blackout_returns_none_when_missing(conn):
    assert get_blackout(conn, "myjob") is None


def test_set_and_get_round_trip(conn):
    set_blackout(conn, "myjob", "02:00", "04:00")
    row = get_blackout(conn, "myjob")
    assert row is not None
    assert row["job_name"] == "myjob"
    assert row["start_time"] == "02:00"
    assert row["end_time"] == "04:00"
    assert row["days_of_week"] == "*"


def test_set_blackout_overwrites_existing(conn):
    set_blackout(conn, "myjob", "02:00", "04:00")
    set_blackout(conn, "myjob", "06:00", "07:00")
    row = get_blackout(conn, "myjob")
    assert row["start_time"] == "06:00"
    assert row["end_time"] == "07:00"


def test_set_blackout_stores_days_of_week(conn):
    set_blackout(conn, "myjob", "22:00", "23:59", days_of_week="Sat,Sun")
    row = get_blackout(conn, "myjob")
    assert row["days_of_week"] == "Sat,Sun"


def test_set_blackout_multiple_labels(conn):
    set_blackout(conn, "myjob", "01:00", "02:00", label="night")
    set_blackout(conn, "myjob", "12:00", "13:00", label="lunch")
    assert get_blackout(conn, "myjob", "night")["start_time"] == "01:00"
    assert get_blackout(conn, "myjob", "lunch")["start_time"] == "12:00"


# ---------------------------------------------------------------------------
# delete_blackout
# ---------------------------------------------------------------------------

def test_delete_blackout_removes_entry(conn):
    set_blackout(conn, "myjob", "02:00", "04:00")
    delete_blackout(conn, "myjob")
    assert get_blackout(conn, "myjob") is None


def test_delete_blackout_only_removes_specified_label(conn):
    set_blackout(conn, "myjob", "01:00", "02:00", label="a")
    set_blackout(conn, "myjob", "03:00", "04:00", label="b")
    delete_blackout(conn, "myjob", label="a")
    assert get_blackout(conn, "myjob", "a") is None
    assert get_blackout(conn, "myjob", "b") is not None


# ---------------------------------------------------------------------------
# list_blackouts
# ---------------------------------------------------------------------------

def test_list_blackouts_empty_when_none(conn):
    assert list_blackouts(conn, "myjob") == []


def test_list_blackouts_returns_all_entries(conn):
    set_blackout(conn, "myjob", "01:00", "02:00", label="a")
    set_blackout(conn, "myjob", "03:00", "04:00", label="b")
    rows = list_blackouts(conn, "myjob")
    assert len(rows) == 2
    labels = {r["label"] for r in rows}
    assert labels == {"a", "b"}


# ---------------------------------------------------------------------------
# is_blacked_out
# ---------------------------------------------------------------------------

def test_is_blacked_out_false_when_no_windows(conn):
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 3, 3, 0)) is False


def test_is_blacked_out_true_within_window(conn):
    set_blackout(conn, "myjob", "02:00", "04:00")
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 3, 3, 0)) is True


def test_is_blacked_out_false_outside_window(conn):
    set_blackout(conn, "myjob", "02:00", "04:00")
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 3, 5, 0)) is False


def test_is_blacked_out_respects_days_of_week(conn):
    # 2024-06-03 is a Monday
    set_blackout(conn, "myjob", "02:00", "04:00", days_of_week="Sat,Sun")
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 3, 3, 0)) is False


def test_is_blacked_out_true_on_matching_day(conn):
    # 2024-06-01 is a Saturday
    set_blackout(conn, "myjob", "02:00", "04:00", days_of_week="Sat,Sun")
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 1, 3, 0)) is True


def test_is_blacked_out_any_window_triggers(conn):
    set_blackout(conn, "myjob", "10:00", "11:00", label="morning")
    set_blackout(conn, "myjob", "22:00", "23:00", label="night")
    assert is_blacked_out(conn, "myjob", at=datetime(2024, 6, 3, 22, 30)) is True
