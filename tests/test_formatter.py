"""Tests for crontrace.formatter."""

import pytest
from crontrace.formatter import (
    _format_duration,
    _format_status,
    format_row,
    format_table,
)


@pytest.mark.parametrize("seconds,expected", [
    (0.005, "5ms"),
    (0.999, "999ms"),
    (1.5, "1.50s"),
    (59.0, "59.00s"),
    (90.0, "1m 30s"),
    (3661.0, "61m 1s"),
])
def test_format_duration(seconds, expected):
    assert _format_duration(seconds) == expected


def test_format_status_zero_is_ok():
    assert _format_status(0) == "OK"


def test_format_status_nonzero_is_fail():
    assert _format_status(1) == "FAIL"
    assert _format_status(127) == "FAIL"


def test_format_row_contains_key_fields():
    record = {
        "started_at": "2024-01-15 08:00:00",
        "command": "echo hello",
        "exit_code": 0,
        "duration_seconds": 0.042,
    }
    row = format_row(record)
    assert "OK" in row
    assert "echo hello" in row
    assert "2024-01-15 08:00:00" in row
    assert "42ms" in row


def test_format_row_failed_command():
    record = {
        "started_at": "2024-01-15 09:00:00",
        "command": "false",
        "exit_code": 1,
        "duration_seconds": 1.23,
    }
    row = format_row(record)
    assert "FAIL" in row


def test_format_row_returns_string():
    """format_row should always return a plain string."""
    record = {
        "started_at": "2024-01-15 08:00:00",
        "command": "echo hello",
        "exit_code": 0,
        "duration_seconds": 0.042,
    }
    assert isinstance(format_row(record), str)


def test_format_table_empty():
    output = format_table([])
    assert "no records found" in output


def test_format_table_contains_all_records():
    records = [
        {"started_at": "2024-01-15 08:00:00", "command": "job_a", "exit_code": 0, "duration_seconds": 1.0},
        {"started_at": "2024-01-15 09:00:00", "command": "job_b", "exit_code": 2, "duration_seconds": 0.5},
    ]
    output = format_table(records)
    assert "job_a" in output
    assert "job_b" in output
    assert "2 record(s) shown" in output


def test_format_table_single_record_count():
    """format_table should report exactly 1 record when given a single entry."""
    records = [
        {"started_at": "2024-01-15 08:00:00", "command": "job_a", "exit_code": 0, "duration_seconds": 1.0},
    ]
    output = format_table(records)
    assert "1 record(s) shown" in output


def test_format_table_custom_title():
    output = format_table([], title="My Jobs")
    assert "My Jobs" in output
