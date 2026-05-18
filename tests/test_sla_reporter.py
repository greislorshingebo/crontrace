import pytest
from crontrace.sla_reporter import (
    render_sla_row,
    render_sla_table,
    render_sla_evaluation,
)


def _entry(**kwargs):
    defaults = {
        "job_name": "backup-daily",
        "max_duration": 120.0,
        "min_success_rate": 0.95,
        "note": None,
    }
    defaults.update(kwargs)
    return defaults


def test_render_row_contains_job_name():
    row = render_sla_row(_entry(job_name="my-job"))
    assert "my-job" in row


def test_render_row_contains_max_duration_seconds():
    row = render_sla_row(_entry(max_duration=45.0))
    assert "45.0s" in row


def test_render_row_contains_max_duration_minutes():
    row = render_sla_row(_entry(max_duration=180.0))
    assert "3.0m" in row


def test_render_row_contains_min_success_rate():
    row = render_sla_row(_entry(min_success_rate=0.9))
    assert "90%" in row


def test_render_row_contains_note():
    row = render_sla_row(_entry(note="critical path"))
    assert "critical path" in row


def test_render_row_none_note_shows_empty():
    row = render_sla_row(_entry(note=None))
    # just ensure it doesn't crash and has job name
    assert "backup-daily" in row


def test_render_row_truncates_long_job_name():
    long_name = "a" * 50
    row = render_sla_row(_entry(job_name=long_name))
    assert "…" in row


def test_render_table_contains_header():
    table = render_sla_table([])
    assert "JOB" in table
    assert "MAX DUR" in table
    assert "MIN RATE" in table


def test_render_table_empty_shows_placeholder():
    table = render_sla_table([])
    assert "no SLAs" in table


def test_render_table_contains_entry():
    entries = [_entry(job_name="nightly-sync")]
    table = render_sla_table(entries)
    assert "nightly-sync" in table


def test_render_table_multiple_entries():
    entries = [_entry(job_name="job-a"), _entry(job_name="job-b")]
    table = render_sla_table(entries)
    assert "job-a" in table
    assert "job-b" in table


def test_render_evaluation_contains_job_name():
    sla = {"max_duration": 60.0, "min_success_rate": 0.9}
    result = {"duration_ok": True, "success_rate_ok": True, "avg_duration": 30.0, "success_rate": 1.0}
    text = render_sla_evaluation("my-job", sla, result)
    assert "my-job" in text


def test_render_evaluation_shows_checkmark_when_ok():
    sla = {"max_duration": 60.0, "min_success_rate": 0.9}
    result = {"duration_ok": True, "success_rate_ok": True, "avg_duration": 30.0, "success_rate": 1.0}
    text = render_sla_evaluation("job", sla, result)
    assert "✓" in text


def test_render_evaluation_shows_cross_when_fail():
    sla = {"max_duration": 10.0, "min_success_rate": 1.0}
    result = {"duration_ok": False, "success_rate_ok": False, "avg_duration": 90.0, "success_rate": 0.5}
    text = render_sla_evaluation("job", sla, result)
    assert "✗" in text


def test_render_evaluation_shows_none_duration_as_dash():
    sla = {"max_duration": 60.0, "min_success_rate": 1.0}
    result = {"duration_ok": True, "success_rate_ok": True, "avg_duration": None, "success_rate": None}
    text = render_sla_evaluation("job", sla, result)
    assert "—" in text
