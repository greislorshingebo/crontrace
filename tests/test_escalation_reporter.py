"""Tests for crontrace.escalation_reporter."""

import pytest

from crontrace.escalation_reporter import (
    render_escalation_row,
    render_escalation_table,
)


def _entry(**kwargs) -> dict:
    base = {
        "job_name": "nightly_backup",
        "threshold": 3,
        "contact": "ops@example.com",
        "enabled": True,
        "note": None,
    }
    base.update(kwargs)
    return base


def test_render_row_contains_job_name():
    row = render_escalation_row(_entry())
    assert "nightly_backup" in row


def test_render_row_contains_threshold():
    row = render_escalation_row(_entry(threshold=7))
    assert "7" in row


def test_render_row_shows_yes_when_enabled():
    row = render_escalation_row(_entry(enabled=True))
    assert "yes" in row


def test_render_row_shows_no_when_disabled():
    row = render_escalation_row(_entry(enabled=False))
    assert "no" in row


def test_render_row_contains_contact():
    row = render_escalation_row(_entry(contact="sre@example.com"))
    assert "sre@example.com" in row


def test_render_row_none_contact_shows_dash():
    row = render_escalation_row(_entry(contact=None))
    assert "-" in row


def test_render_row_contains_note():
    row = render_escalation_row(_entry(note="page on-call"))
    assert "page on-call" in row


def test_render_row_none_note_shows_dash():
    row = render_escalation_row(_entry(note=None))
    assert "-" in row


def test_render_row_truncates_long_job_name():
    long_name = "j" * 50
    row = render_escalation_row(_entry(job_name=long_name))
    assert "…" in row


def test_render_table_empty_returns_message():
    result = render_escalation_table([])
    assert "No escalation policies" in result


def test_render_table_contains_job_name():
    entries = [_entry(job_name="sync_job")]
    result = render_escalation_table(entries)
    assert "sync_job" in result


def test_render_table_contains_header():
    entries = [_entry()]
    result = render_escalation_table(entries)
    assert "JOB" in result
    assert "THRESHOLD" in result
    assert "CONTACT" in result


def test_render_table_multiple_entries():
    entries = [
        _entry(job_name="alpha", threshold=2),
        _entry(job_name="beta", threshold=5),
    ]
    result = render_escalation_table(entries)
    assert "alpha" in result
    assert "beta" in result
