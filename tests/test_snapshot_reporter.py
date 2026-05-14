"""Tests for crontrace.snapshot_reporter."""

import pytest

from crontrace.snapshot_reporter import (
    render_snapshot_row,
    render_snapshot_table,
)


def _entry(**kwargs):
    base = {
        "job_name": "daily-backup",
        "exit_code": 0,
        "duration": 8.42,
        "stdout": "backup complete",
        "captured_at": "2024-01-15T10:00:00",
    }
    base.update(kwargs)
    return base


def test_render_row_contains_job_name():
    row = render_snapshot_row(_entry())
    assert "daily-backup" in row


def test_render_row_shows_ok_for_zero_exit():
    row = render_snapshot_row(_entry(exit_code=0))
    assert "OK" in row


def test_render_row_shows_code_for_nonzero_exit():
    row = render_snapshot_row(_entry(exit_code=2))
    assert "2" in row


def test_render_row_contains_duration():
    row = render_snapshot_row(_entry(duration=8.42))
    assert "8.42" in row


def test_render_row_none_duration_shows_dash():
    row = render_snapshot_row(_entry(duration=None))
    assert "-" in row


def test_render_row_contains_captured_at():
    row = render_snapshot_row(_entry(captured_at="2024-01-15T10:00:00"))
    assert "2024-01-15" in row


def test_render_row_truncates_long_job_name():
    long_name = "x" * 50
    row = render_snapshot_row(_entry(job_name=long_name))
    assert "…" in row


def test_render_table_contains_header():
    table = render_snapshot_table([_entry()])
    assert "JOB" in table
    assert "CODE" in table
    assert "DURATION" in table


def test_render_table_contains_job_name():
    table = render_snapshot_table([_entry(job_name="cleanup")])
    assert "cleanup" in table


def test_render_table_empty_shows_placeholder():
    table = render_snapshot_table([])
    assert "no snapshots" in table


def test_render_table_with_job_name_in_title():
    table = render_snapshot_table([_entry()], job_name="daily-backup")
    assert "daily-backup" in table


def test_render_table_default_title():
    table = render_snapshot_table([])
    assert "All Snapshots" in table


def test_render_table_multiple_rows():
    entries = [_entry(job_name="a"), _entry(job_name="b")]
    table = render_snapshot_table(entries)
    assert "a" in table
    assert "b" in table
