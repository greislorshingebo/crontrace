"""Tests for crontrace.job_watchers and crontrace.watcher_reporter."""

import sqlite3
import pytest

from crontrace.job_watchers import (
    add_watcher,
    remove_watcher,
    list_watchers,
    watchers_for_event,
)
from crontrace.watcher_reporter import render_watcher_row, render_watcher_table


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_list_watchers_empty_when_none(conn):
    assert list_watchers(conn, "backup") == []


def test_add_and_list_watcher(conn):
    add_watcher(conn, "backup", "alice@example.com")
    rows = list_watchers(conn, "backup")
    assert len(rows) == 1
    assert rows[0]["watcher"] == "alice@example.com"


def test_add_watcher_normalises_case(conn):
    add_watcher(conn, "backup", "Alice@Example.COM")
    rows = list_watchers(conn, "backup")
    assert rows[0]["watcher"] == "alice@example.com"


def test_add_duplicate_watcher_updates_notify_on(conn):
    add_watcher(conn, "backup", "alice@example.com", notify_on="failure")
    add_watcher(conn, "backup", "alice@example.com", notify_on="always")
    rows = list_watchers(conn, "backup")
    assert len(rows) == 1
    assert rows[0]["notify_on"] == "always"


def test_add_watcher_invalid_notify_on_raises(conn):
    with pytest.raises(ValueError):
        add_watcher(conn, "backup", "alice@example.com", notify_on="never")


def test_remove_watcher_returns_true_when_removed(conn):
    add_watcher(conn, "backup", "alice@example.com")
    assert remove_watcher(conn, "backup", "alice@example.com") is True
    assert list_watchers(conn, "backup") == []


def test_remove_watcher_returns_false_when_missing(conn):
    assert remove_watcher(conn, "backup", "nobody@example.com") is False


def test_list_watchers_isolated_per_job(conn):
    add_watcher(conn, "job_a", "alice@example.com")
    add_watcher(conn, "job_b", "bob@example.com")
    assert len(list_watchers(conn, "job_a")) == 1
    assert list_watchers(conn, "job_a")[0]["watcher"] == "alice@example.com"


def test_watchers_for_event_failure(conn):
    add_watcher(conn, "backup", "alice@example.com", notify_on="failure")
    add_watcher(conn, "backup", "bob@example.com", notify_on="success")
    add_watcher(conn, "backup", "carol@example.com", notify_on="always")
    result = watchers_for_event(conn, "backup", "failure")
    assert "alice@example.com" in result
    assert "carol@example.com" in result
    assert "bob@example.com" not in result


def test_watchers_for_event_success(conn):
    add_watcher(conn, "backup", "alice@example.com", notify_on="failure")
    add_watcher(conn, "backup", "bob@example.com", notify_on="success")
    result = watchers_for_event(conn, "backup", "success")
    assert "bob@example.com" in result
    assert "alice@example.com" not in result


def test_render_watcher_row_contains_watcher_name():
    entry = {"job_name": "backup", "watcher": "alice@example.com", "notify_on": "failure", "added_at": "2024-01-01T00:00:00"}
    row = render_watcher_row(entry)
    assert "alice@example.com" in row


def test_render_watcher_row_contains_icon():
    entry = {"job_name": "backup", "watcher": "alice@example.com", "notify_on": "always", "added_at": "2024-01-01T00:00:00"}
    row = render_watcher_row(entry)
    assert "★" in row


def test_render_watcher_table_no_entries():
    result = render_watcher_table("backup", [])
    assert "No watchers" in result


def test_render_watcher_table_contains_job_name():
    entries = [{"job_name": "backup", "watcher": "alice@example.com", "notify_on": "failure", "added_at": "2024-01-01"}]
    result = render_watcher_table("backup", entries)
    assert "backup" in result
    assert "alice@example.com" in result
