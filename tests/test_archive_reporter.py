"""Tests for crontrace.archive_reporter."""

import pytest

from crontrace.archive_reporter import (
    render_archive_row,
    render_archive_table,
)


def _entry(**kwargs):
    base = {
        "id": 1,
        "job_name": "backup-db",
        "started_at": "2024-01-15T02:00:01",
        "duration": 0.83,
        "exit_code": 0,
        "stdout": "",
        "archived_at": "2024-02-01T00:00:00",
    }
    base.update(kwargs)
    return base


def test_render_row_contains_job_name():
    row = render_archive_row(_entry())
    assert "backup-db" in row


def test_render_row_contains_started_at():
    row = render_archive_row(_entry())
    assert "2024-01-15T02:00:01" in row


def test_render_row_shows_ok_for_zero_exit():
    row = render_archive_row(_entry(exit_code=0))
    assert "OK" in row


def test_render_row_shows_fail_for_nonzero_exit():
    row = render_archive_row(_entry(exit_code=2))
    assert "FAIL(2)" in row


def test_render_row_contains_duration():
    row = render_archive_row(_entry(duration=1.23))
    assert "1.23s" in row


def test_render_row_dash_for_none_duration():
    row = render_archive_row(_entry(duration=None))
    assert "-" in row


def test_render_row_contains_archived_at():
    row = render_archive_row(_entry())
    assert "2024-02-01T00:00:00" in row


def test_render_table_contains_title():
    table = render_archive_table("backup-db", [])
    assert "backup-db" in table


def test_render_table_shows_record_count():
    rows = [_entry(), _entry(id=2)]
    table = render_archive_table("backup-db", rows)
    assert "2 record(s)" in table


def test_render_table_empty_shows_placeholder():
    table = render_archive_table("backup-db", [])
    assert "no archived records" in table


def test_render_table_contains_header():
    table = render_archive_table("backup-db", [_entry()])
    assert "STARTED" in table
    assert "STATUS" in table
    assert "ARCHIVED" in table


def test_render_row_truncates_long_job_name():
    long_name = "a" * 40
    row = render_archive_row(_entry(job_name=long_name))
    assert "…" in row
