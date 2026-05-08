"""Tests for crontrace.priority_reporter."""

from crontrace.priority_reporter import (
    render_priority_row,
    render_priority_table,
)


def _entry(job_name="backup-db", priority="high", updated_at="2024-06-01T02:00:00"):
    return {"job_name": job_name, "priority": priority, "updated_at": updated_at}


def test_render_row_contains_job_name():
    row = render_priority_row(_entry(job_name="my-job"))
    assert "my-job" in row


def test_render_row_contains_priority():
    row = render_priority_row(_entry(priority="critical"))
    assert "critical" in row


def test_render_row_contains_icon_for_critical():
    row = render_priority_row(_entry(priority="critical"))
    assert "🔴" in row


def test_render_row_contains_icon_for_low():
    row = render_priority_row(_entry(priority="low"))
    assert "⚪" in row


def test_render_row_contains_updated_at():
    row = render_priority_row(_entry(updated_at="2024-06-01T02:00:00"))
    assert "2024-06-01" in row


def test_render_row_truncates_long_job_name():
    long_name = "x" * 50
    row = render_priority_row(_entry(job_name=long_name))
    assert "…" in row


def test_render_table_contains_header():
    table = render_priority_table([])
    assert "JOB" in table
    assert "PRIORITY" in table


def test_render_table_empty_shows_placeholder():
    table = render_priority_table([])
    assert "no priorities" in table


def test_render_table_contains_entry():
    entries = [_entry(job_name="sync-data", priority="normal")]
    table = render_priority_table(entries)
    assert "sync-data" in table
    assert "normal" in table


def test_render_table_with_job_name_shows_heading():
    table = render_priority_table([], job_name="backup-db")
    assert "backup-db" in table


def test_render_table_multiple_entries():
    entries = [
        _entry(job_name="job-a", priority="critical"),
        _entry(job_name="job-b", priority="low"),
    ]
    table = render_priority_table(entries)
    assert "job-a" in table
    assert "job-b" in table
