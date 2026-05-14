"""Tests for crontrace.quota_reporter."""

from crontrace.quota_reporter import (
    render_quota_row,
    render_quota_table,
)


def _entry(job="backup", max_runs=5, window="day"):
    return {"job_name": job, "max_runs": max_runs, "window": window}


def test_render_row_contains_job_name():
    row = render_quota_row(_entry(job="nightly-backup"))
    assert "nightly-backup" in row


def test_render_row_contains_max_runs():
    row = render_quota_row(_entry(max_runs=12))
    assert "12" in row


def test_render_row_contains_window():
    row = render_quota_row(_entry(window="week"))
    assert "week" in row


def test_render_row_truncates_long_job_name():
    long_name = "x" * 50
    row = render_quota_row(_entry(job=long_name))
    assert "…" in row


def test_render_table_contains_header():
    table = render_quota_table([_entry()])
    assert "JOB" in table
    assert "MAX RUNS" in table
    assert "WINDOW" in table


def test_render_table_contains_entry():
    table = render_quota_table([_entry(job="cleanup", max_runs=3, window="hour")])
    assert "cleanup" in table
    assert "3" in table
    assert "hour" in table


def test_render_table_empty_returns_no_quotas_message():
    result = render_quota_table([])
    assert "No quotas configured" in result


def test_render_table_multiple_entries():
    entries = [
        _entry(job="alpha", max_runs=2, window="hour"),
        _entry(job="beta", max_runs=10, window="day"),
    ]
    table = render_quota_table(entries)
    assert "alpha" in table
    assert "beta" in table


def test_render_table_separator_line_present():
    table = render_quota_table([_entry()])
    lines = table.splitlines()
    assert any(set(line.strip()) <= {"-"} for line in lines)
