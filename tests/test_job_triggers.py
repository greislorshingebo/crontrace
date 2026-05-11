"""Tests for crontrace.job_triggers and crontrace.trigger_reporter."""

import sqlite3
import pytest

from crontrace.job_triggers import (
    record_trigger,
    get_triggers,
    delete_trigger,
    triggers_for_type,
)
from crontrace.trigger_reporter import (
    render_trigger_row,
    render_trigger_table,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# ── job_triggers ────────────────────────────────────────────────────────────


def test_record_trigger_returns_rowid(conn):
    rowid = record_trigger(conn, "backup", "manual")
    assert isinstance(rowid, int) and rowid >= 1


def test_get_triggers_empty_when_none(conn):
    assert get_triggers(conn, "backup") == []


def test_get_triggers_returns_added_entry(conn):
    record_trigger(conn, "backup", "manual", note="ad-hoc run")
    results = get_triggers(conn, "backup")
    assert len(results) == 1
    assert results[0]["job_name"] == "backup"
    assert results[0]["trigger"] == "manual"
    assert results[0]["note"] == "ad-hoc run"


def test_get_triggers_newest_first(conn):
    record_trigger(conn, "backup", "manual")
    record_trigger(conn, "backup", "webhook")
    results = get_triggers(conn, "backup")
    assert results[0]["trigger"] == "webhook"
    assert results[1]["trigger"] == "manual"


def test_get_triggers_isolated_per_job(conn):
    record_trigger(conn, "backup", "manual")
    record_trigger(conn, "cleanup", "schedule")
    assert len(get_triggers(conn, "backup")) == 1
    assert len(get_triggers(conn, "cleanup")) == 1


def test_delete_trigger_removes_entry(conn):
    rowid = record_trigger(conn, "backup", "manual")
    assert delete_trigger(conn, rowid) is True
    assert get_triggers(conn, "backup") == []


def test_delete_trigger_missing_returns_false(conn):
    assert delete_trigger(conn, 9999) is False


def test_record_trigger_invalid_type_raises(conn):
    with pytest.raises(ValueError, match="Unknown trigger type"):
        record_trigger(conn, "backup", "unknown_type")


def test_triggers_for_type_returns_matching(conn):
    record_trigger(conn, "backup", "manual")
    record_trigger(conn, "cleanup", "webhook")
    record_trigger(conn, "report", "manual")
    results = triggers_for_type(conn, "manual")
    assert len(results) == 2
    assert all(r["trigger"] == "manual" for r in results)


def test_triggers_for_type_empty_when_none(conn):
    assert triggers_for_type(conn, "dependency") == []


# ── trigger_reporter ─────────────────────────────────────────────────────────


def _make_entry(**kwargs):
    base = {
        "id": 1,
        "job_name": "backup",
        "trigger": "manual",
        "note": "test note",
        "fired_at": "2024-06-01T12:00:00Z",
    }
    base.update(kwargs)
    return base


def test_render_trigger_row_contains_job_name():
    row = render_trigger_row(_make_entry())
    assert "backup" in row


def test_render_trigger_row_contains_trigger_type():
    row = render_trigger_row(_make_entry(trigger="webhook"))
    assert "webhook" in row


def test_render_trigger_row_none_note_shows_dash():
    row = render_trigger_row(_make_entry(note=None))
    assert "-" in row


def test_render_trigger_table_contains_header(conn):
    record_trigger(conn, "backup", "manual", note="hi")
    entries = get_triggers(conn, "backup")
    table = render_trigger_table("backup", entries)
    assert "Triggers for: backup" in table
    assert "JOB" in table
    assert "TYPE" in table


def test_render_trigger_table_empty_shows_message():
    table = render_trigger_table("backup", [])
    assert "no trigger records" in table


def test_render_trigger_table_no_job_name_shows_all():
    table = render_trigger_table(None, [])
    assert "All Triggers" in table
