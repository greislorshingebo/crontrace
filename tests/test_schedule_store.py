"""Tests for crontrace.schedule_store."""

from __future__ import annotations

import pytest

from crontrace.schedule_store import (
    upsert_schedule,
    fetch_schedule,
    list_schedules,
    delete_schedule,
)


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_schedules.db")


# ---------------------------------------------------------------------------
# upsert + fetch
# ---------------------------------------------------------------------------

def test_fetch_returns_none_when_missing(db_path):
    assert fetch_schedule(db_path, "nonexistent") is None


def test_upsert_and_fetch_round_trip(db_path):
    upsert_schedule(db_path, "backup", "0 2 * * *")
    assert fetch_schedule(db_path, "backup") == "0 2 * * *"


def test_upsert_overwrites_existing(db_path):
    upsert_schedule(db_path, "cleanup", "0 3 * * *")
    upsert_schedule(db_path, "cleanup", "30 3 * * *")
    assert fetch_schedule(db_path, "cleanup") == "30 3 * * *"


# ---------------------------------------------------------------------------
# list_schedules
# ---------------------------------------------------------------------------

def test_list_schedules_empty(db_path):
    assert list_schedules(db_path) == []


def test_list_schedules_returns_all(db_path):
    upsert_schedule(db_path, "alpha", "* * * * *")
    upsert_schedule(db_path, "beta", "0 0 * * *")
    rows = list_schedules(db_path)
    names = [r["job_name"] for r in rows]
    assert "alpha" in names
    assert "beta" in names


def test_list_schedules_contains_expression(db_path):
    upsert_schedule(db_path, "myjob", "*/15 * * * *")
    rows = list_schedules(db_path)
    assert rows[0]["expression"] == "*/15 * * * *"


# ---------------------------------------------------------------------------
# delete_schedule
# ---------------------------------------------------------------------------

def test_delete_existing_returns_true(db_path):
    upsert_schedule(db_path, "todelete", "0 1 * * *")
    assert delete_schedule(db_path, "todelete") is True


def test_delete_removes_record(db_path):
    upsert_schedule(db_path, "gone", "0 4 * * *")
    delete_schedule(db_path, "gone")
    assert fetch_schedule(db_path, "gone") is None


def test_delete_nonexistent_returns_false(db_path):
    assert delete_schedule(db_path, "ghost") is False
