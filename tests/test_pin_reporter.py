"""Tests for crontrace.pin_reporter."""

from crontrace.pin_reporter import render_pin_row, render_pin_table


def _entry(**kwargs):
    base = {
        "job_name": "backup",
        "run_id": 42,
        "note": "golden run",
        "pinned_at": "2024-01-15T08:30:00",
    }
    base.update(kwargs)
    return base


def test_render_row_contains_job_name():
    row = render_pin_row(_entry())
    assert "backup" in row


def test_render_row_contains_run_id():
    row = render_pin_row(_entry(run_id=99))
    assert "99" in row


def test_render_row_contains_note():
    row = render_pin_row(_entry(note="stable baseline"))
    assert "stable baseline" in row


def test_render_row_none_note_shows_dash():
    row = render_pin_row(_entry(note=None))
    assert "-" in row


def test_render_row_contains_pinned_at():
    row = render_pin_row(_entry(pinned_at="2024-03-01T12:00:00"))
    assert "2024-03-01" in row


def test_render_row_truncates_long_job_name():
    long_name = "x" * 60
    row = render_pin_row(_entry(job_name=long_name))
    assert "…" in row


def test_render_row_truncates_long_note():
    long_note = "n" * 80
    row = render_pin_row(_entry(note=long_note))
    assert "…" in row


def test_render_table_empty_returns_message():
    result = render_pin_table([])
    assert "No pinned" in result


def test_render_table_contains_header():
    result = render_pin_table([_entry()])
    assert "JOB" in result
    assert "RUN ID" in result


def test_render_table_contains_all_entries():
    entries = [_entry(job_name="alpha", run_id=1), _entry(job_name="beta", run_id=2)]
    result = render_pin_table(entries)
    assert "alpha" in result
    assert "beta" in result
