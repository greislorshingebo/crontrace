"""Tests for crontrace.job_runbook."""

import sqlite3
import pytest

from crontrace.job_runbook import (
    set_runbook,
    get_runbook,
    delete_runbook,
    list_runbooks,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# get_runbook
# ---------------------------------------------------------------------------

def test_get_runbook_returns_none_when_missing(conn):
    assert get_runbook(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_runbook(conn, "backup", "https://wiki.example.com/backup")
    entry = get_runbook(conn, "backup")
    assert entry is not None
    assert entry["job_name"] == "backup"
    assert entry["url"] == "https://wiki.example.com/backup"


def test_get_runbook_includes_note(conn):
    set_runbook(conn, "deploy", "https://docs.example.com/deploy", note="See section 3")
    entry = get_runbook(conn, "deploy")
    assert entry["note"] == "See section 3"


def test_get_runbook_note_defaults_to_none(conn):
    set_runbook(conn, "cleanup", "https://example.com/cleanup")
    entry = get_runbook(conn, "cleanup")
    assert entry["note"] is None


def test_get_runbook_includes_updated_at(conn):
    set_runbook(conn, "sync", "https://example.com/sync")
    entry = get_runbook(conn, "sync")
    assert "updated_at" in entry
    assert entry["updated_at"].endswith("Z")


# ---------------------------------------------------------------------------
# set_runbook (overwrite)
# ---------------------------------------------------------------------------

def test_set_runbook_overwrites_existing(conn):
    set_runbook(conn, "report", "https://old.example.com")
    set_runbook(conn, "report", "https://new.example.com", note="updated")
    entry = get_runbook(conn, "report")
    assert entry["url"] == "https://new.example.com"
    assert entry["note"] == "updated"


def test_set_runbook_strips_whitespace(conn):
    set_runbook(conn, "  trim  ", "  https://example.com/trim  ")
    entry = get_runbook(conn, "trim")
    assert entry is not None
    assert entry["url"] == "https://example.com/trim"


# ---------------------------------------------------------------------------
# delete_runbook
# ---------------------------------------------------------------------------

def test_delete_runbook_returns_true_when_exists(conn):
    set_runbook(conn, "old_job", "https://example.com/old")
    assert delete_runbook(conn, "old_job") is True


def test_delete_runbook_returns_false_when_missing(conn):
    assert delete_runbook(conn, "ghost") is False


def test_delete_runbook_removes_entry(conn):
    set_runbook(conn, "temp", "https://example.com/temp")
    delete_runbook(conn, "temp")
    assert get_runbook(conn, "temp") is None


# ---------------------------------------------------------------------------
# list_runbooks
# ---------------------------------------------------------------------------

def test_list_runbooks_empty_returns_empty_list(conn):
    assert list_runbooks(conn) == []


def test_list_runbooks_returns_all_entries(conn):
    set_runbook(conn, "alpha", "https://example.com/alpha")
    set_runbook(conn, "beta", "https://example.com/beta")
    entries = list_runbooks(conn)
    assert len(entries) == 2


def test_list_runbooks_ordered_by_job_name(conn):
    set_runbook(conn, "zebra", "https://example.com/z")
    set_runbook(conn, "apple", "https://example.com/a")
    names = [e["job_name"] for e in list_runbooks(conn)]
    assert names == sorted(names)
