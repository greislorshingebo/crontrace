"""Tests for crontrace.catalog_reporter."""

import pytest

from crontrace.catalog_reporter import (
    render_catalog_row,
    render_catalog_table,
)


def _entry(**kwargs):
    base = {
        "job_name": "backup",
        "command": "/bin/backup.sh",
        "schedule": "0 2 * * *",
        "description": "nightly backup",
        "owner": "ops",
        "created_at": "2024-01-01 02:00:00",
    }
    base.update(kwargs)
    return base


def test_render_row_contains_job_name():
    row = render_catalog_row(_entry())
    assert "backup" in row


def test_render_row_contains_command():
    row = render_catalog_row(_entry())
    assert "/bin/backup.sh" in row


def test_render_row_contains_schedule():
    row = render_catalog_row(_entry())
    assert "0 2 * * *" in row


def test_render_row_contains_owner():
    row = render_catalog_row(_entry())
    assert "ops" in row


def test_render_row_none_schedule_shows_dash():
    row = render_catalog_row(_entry(schedule=None))
    assert "-" in row


def test_render_row_none_owner_shows_dash():
    row = render_catalog_row(_entry(owner=None))
    assert "-" in row


def test_render_table_contains_header():
    table = render_catalog_table([_entry()])
    assert "JOB NAME" in table
    assert "COMMAND" in table
    assert "SCHEDULE" in table
    assert "OWNER" in table


def test_render_table_empty_shows_placeholder():
    table = render_catalog_table([])
    assert "no jobs registered" in table


def test_render_table_multiple_rows():
    entries = [
        _entry(job_name="alpha", command="/bin/alpha.sh"),
        _entry(job_name="beta", command="/bin/beta.sh"),
    ]
    table = render_catalog_table(entries)
    assert "alpha" in table
    assert "beta" in table


def test_render_table_long_name_is_truncated():
    long_name = "a" * 50
    row = render_catalog_row(_entry(job_name=long_name))
    # truncated to 24 chars with ellipsis marker
    assert "…" in row
