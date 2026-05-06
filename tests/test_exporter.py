"""Tests for crontrace.exporter."""

from __future__ import annotations

import json
import sqlite3

import pytest

from crontrace.exporter import export_csv, export_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rows():
    """Return a list of sqlite3.Row-like objects via an in-memory DB."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE executions (
            id INTEGER PRIMARY KEY,
            job TEXT,
            started_at TEXT,
            duration_s REAL,
            exit_code INTEGER
        )
        """
    )
    conn.execute(
        "INSERT INTO executions (job, started_at, duration_s, exit_code) VALUES (?, ?, ?, ?)",
        ("backup", "2024-01-01T00:00:00", 1.5, 0),
    )
    conn.execute(
        "INSERT INTO executions (job, started_at, duration_s, exit_code) VALUES (?, ?, ?, ?)",
        ("cleanup", "2024-01-02T00:00:00", 0.3, 1),
    )
    conn.commit()
    return conn.execute("SELECT * FROM executions ORDER BY id").fetchall()


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def test_export_json_returns_valid_json():
    rows = _make_rows()
    result = export_json(rows)
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 2


def test_export_json_contains_expected_fields():
    rows = _make_rows()
    parsed = json.loads(export_json(rows))
    first = parsed[0]
    assert first["job"] == "backup"
    assert first["exit_code"] == 0
    assert first["duration_s"] == pytest.approx(1.5)


def test_export_json_empty_rows():
    result = export_json([])
    assert json.loads(result) == []


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def test_export_csv_returns_header_and_rows():
    rows = _make_rows()
    result = export_csv(rows)
    lines = result.strip().splitlines()
    assert lines[0] == "id,job,started_at,duration_s,exit_code"
    assert len(lines) == 3  # header + 2 data rows


def test_export_csv_contains_job_names():
    rows = _make_rows()
    result = export_csv(rows)
    assert "backup" in result
    assert "cleanup" in result


def test_export_csv_empty_rows():
    result = export_csv([])
    assert result == ""
