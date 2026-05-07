"""Tests for crontrace.job_search and crontrace.search_reporter."""

from __future__ import annotations

import sqlite3
import pytest

from crontrace.job_search import (
    search_by_name,
    search_by_exit_code,
    search_output,
    search_combined,
)
from crontrace.search_reporter import render_search_results


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.execute(
        """
        CREATE TABLE executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT,
            started_at TEXT,
            exit_code INTEGER,
            duration_s REAL,
            stdout TEXT,
            stderr TEXT
        )
        """
    )
    rows = [
        ("backup-db", "2024-05-01T02:00:00", 0, 4.21, "done", ""),
        ("backup-files", "2024-05-01T02:05:00", 0, 7.83, "copied 10 files", ""),
        ("cleanup", "2024-05-01T03:00:00", 1, 1.5, "", "permission denied"),
        ("report-gen", "2024-05-01T04:00:00", 0, 2.0, "report ready", ""),
    ]
    c.executemany(
        "INSERT INTO executions(job_name,started_at,exit_code,duration_s,stdout,stderr) VALUES(?,?,?,?,?,?)",
        rows,
    )
    c.commit()
    return c


def test_search_by_name_returns_matches(conn):
    results = search_by_name(conn, "backup")
    assert len(results) == 2
    names = {r["job_name"] for r in results}
    assert names == {"backup-db", "backup-files"}


def test_search_by_name_case_insensitive(conn):
    results = search_by_name(conn, "BACKUP")
    assert len(results) == 2


def test_search_by_name_no_match_returns_empty(conn):
    results = search_by_name(conn, "nonexistent")
    assert results == []


def test_search_by_exit_code_zero(conn):
    results = search_by_exit_code(conn, 0)
    assert len(results) == 3


def test_search_by_exit_code_nonzero(conn):
    results = search_by_exit_code(conn, 1)
    assert len(results) == 1
    assert results[0]["job_name"] == "cleanup"


def test_search_output_finds_stdout(conn):
    results = search_output(conn, "files")
    assert any(r["job_name"] == "backup-files" for r in results)


def test_search_output_finds_stderr(conn):
    results = search_output(conn, "permission")
    assert len(results) == 1
    assert results[0]["job_name"] == "cleanup"


def test_search_output_case_insensitive(conn):
    results = search_output(conn, "DONE")
    assert any(r["job_name"] == "backup-db" for r in results)


def test_search_combined_name_and_code(conn):
    results = search_combined(conn, name="backup", exit_code=0)
    assert len(results) == 2


def test_search_combined_no_filters_returns_all(conn):
    results = search_combined(conn)
    assert len(results) == 4


def test_search_combined_name_and_output(conn):
    results = search_combined(conn, name="backup", output_term="files")
    assert len(results) == 1
    assert results[0]["job_name"] == "backup-files"


def test_render_search_results_contains_header(conn):
    rows = search_by_name(conn, "backup")
    output = render_search_results(rows, "name~backup")
    assert "JOB" in output
    assert "STARTED" in output
    assert "CODE" in output


def test_render_search_results_shows_count(conn):
    rows = search_by_name(conn, "backup")
    output = render_search_results(rows)
    assert "2 result(s)" in output


def test_render_search_results_empty(conn):
    output = render_search_results([], "name~ghost")
    assert "no results" in output
    assert "0 result(s)" in output
