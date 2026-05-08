"""Tests for crontrace.job_notes."""

import sqlite3
import pytest

from crontrace.job_notes import (
    add_note,
    get_notes,
    delete_note,
    notes_for_job,
)

TS = "2024-06-01T10:00:00"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_notes_empty_when_none(conn):
    result = get_notes(conn, exec_id=1)
    assert result == []


def test_add_note_returns_rowid(conn):
    rowid = add_note(conn, exec_id=1, job_name="backup", note="all good", created_at=TS)
    assert isinstance(rowid, int)
    assert rowid >= 1


def test_get_notes_returns_added_note(conn):
    add_note(conn, exec_id=5, job_name="backup", note="manual check", created_at=TS)
    notes = get_notes(conn, exec_id=5)
    assert len(notes) == 1
    assert notes[0]["note"] == "manual check"
    assert notes[0]["exec_id"] == 5
    assert notes[0]["job_name"] == "backup"


def test_get_notes_multiple_ordered_oldest_first(conn):
    add_note(conn, exec_id=2, job_name="sync", note="first", created_at="2024-01-01T00:00:00")
    add_note(conn, exec_id=2, job_name="sync", note="second", created_at="2024-01-02T00:00:00")
    notes = get_notes(conn, exec_id=2)
    assert len(notes) == 2
    assert notes[0]["note"] == "first"
    assert notes[1]["note"] == "second"


def test_get_notes_isolated_per_exec_id(conn):
    add_note(conn, exec_id=10, job_name="job_a", note="for 10", created_at=TS)
    add_note(conn, exec_id=11, job_name="job_a", note="for 11", created_at=TS)
    assert len(get_notes(conn, exec_id=10)) == 1
    assert len(get_notes(conn, exec_id=11)) == 1


def test_delete_note_removes_row(conn):
    nid = add_note(conn, exec_id=3, job_name="prune", note="temp", created_at=TS)
    assert delete_note(conn, nid) is True
    assert get_notes(conn, exec_id=3) == []


def test_delete_note_returns_false_when_missing(conn):
    assert delete_note(conn, 9999) is False


def test_add_note_strips_whitespace(conn):
    add_note(conn, exec_id=7, job_name="trim", note="  spaces  ", created_at=TS)
    notes = get_notes(conn, exec_id=7)
    assert notes[0]["note"] == "spaces"


def test_add_note_raises_on_empty_string(conn):
    with pytest.raises(ValueError):
        add_note(conn, exec_id=8, job_name="bad", note="   ", created_at=TS)


def test_notes_for_job_returns_all_executions(conn):
    add_note(conn, exec_id=20, job_name="deploy", note="exec 20", created_at=TS)
    add_note(conn, exec_id=21, job_name="deploy", note="exec 21", created_at=TS)
    add_note(conn, exec_id=22, job_name="other", note="different job", created_at=TS)
    results = notes_for_job(conn, "deploy")
    assert len(results) == 2
    assert all(r["job_name"] == "deploy" for r in results)


def test_notes_for_job_empty_when_no_match(conn):
    add_note(conn, exec_id=30, job_name="alpha", note="note", created_at=TS)
    assert notes_for_job(conn, "beta") == []
