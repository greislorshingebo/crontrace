"""Tests for crontrace.job_badges."""

import sqlite3
import pytest

from crontrace.job_badges import (
    BADGE_FAIL,
    BADGE_OK,
    BADGE_UNKNOWN,
    BADGE_WARN,
    _status_from_rows,
    get_badge_color,
    get_badge_status,
    render_badge_json,
    render_badge_text,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.execute(
        """
        CREATE TABLE executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            exit_code INTEGER NOT NULL,
            started_at TEXT NOT NULL
        )
        """
    )
    c.commit()
    return c


def _insert(conn, job_name, exit_code, started_at="2024-01-01T00:00:00"):
    conn.execute(
        "INSERT INTO executions (job_name, exit_code, started_at) VALUES (?, ?, ?)",
        (job_name, exit_code, started_at),
    )
    conn.commit()


# --- _status_from_rows ---

def test_status_from_rows_empty_returns_unknown():
    assert _status_from_rows([]) == BADGE_UNKNOWN


def test_status_from_rows_all_success_returns_ok():
    rows = [{"exit_code": 0}] * 3
    assert _status_from_rows(rows) == BADGE_OK


def test_status_from_rows_all_fail_returns_fail():
    rows = [{"exit_code": 1}] * 5
    assert _status_from_rows(rows) == BADGE_FAIL


def test_status_from_rows_mixed_returns_warn():
    rows = [{"exit_code": 0}, {"exit_code": 1}, {"exit_code": 0}]
    assert _status_from_rows(rows) == BADGE_WARN


# --- get_badge_status ---

def test_get_badge_status_no_rows_returns_unknown(conn):
    assert get_badge_status(conn, "missing_job") == BADGE_UNKNOWN


def test_get_badge_status_all_success(conn):
    for i in range(3):
        _insert(conn, "backup", 0, f"2024-01-0{i+1}T00:00:00")
    assert get_badge_status(conn, "backup") == BADGE_OK


def test_get_badge_status_all_fail(conn):
    for i in range(5):
        _insert(conn, "sync", 1, f"2024-01-0{i+1}T00:00:00")
    assert get_badge_status(conn, "sync") == BADGE_FAIL


def test_get_badge_status_mixed_returns_warn(conn):
    _insert(conn, "report", 0, "2024-01-01T00:00:00")
    _insert(conn, "report", 1, "2024-01-02T00:00:00")
    _insert(conn, "report", 0, "2024-01-03T00:00:00")
    assert get_badge_status(conn, "report") == BADGE_WARN


# --- get_badge_color ---

def test_get_badge_color_ok():
    assert get_badge_color(BADGE_OK) == "brightgreen"


def test_get_badge_color_fail():
    assert get_badge_color(BADGE_FAIL) == "red"


def test_get_badge_color_warn():
    assert get_badge_color(BADGE_WARN) == "yellow"


def test_get_badge_color_unknown():
    assert get_badge_color(BADGE_UNKNOWN) == "lightgrey"


# --- render_badge_json ---

def test_render_badge_json_contains_job_name():
    result = render_badge_json("my_job", BADGE_OK)
    assert result["label"] == "my_job"


def test_render_badge_json_contains_status():
    result = render_badge_json("my_job", BADGE_FAIL)
    assert result["message"] == BADGE_FAIL


def test_render_badge_json_schema_version():
    result = render_badge_json("x", BADGE_OK)
    assert result["schemaVersion"] == 1


# --- render_badge_text ---

def test_render_badge_text_contains_job_name():
    text = render_badge_text("nightly", BADGE_OK)
    assert "nightly" in text


def test_render_badge_text_contains_status():
    text = render_badge_text("nightly", BADGE_FAIL)
    assert BADGE_FAIL in text
