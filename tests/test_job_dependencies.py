"""Tests for crontrace.job_dependencies."""

import sqlite3
import pytest

from crontrace.job_dependencies import (
    add_dependency,
    remove_dependency,
    list_dependencies,
    dependents_of,
    dependencies_satisfied,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    # Create a minimal executions table so dependencies_satisfied can query it.
    c.execute(
        """
        CREATE TABLE executions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name   TEXT NOT NULL,
            started_at TEXT NOT NULL,
            exit_code  INTEGER NOT NULL,
            duration   REAL NOT NULL
        )
        """
    )
    c.commit()
    yield c
    c.close()


def test_add_and_list_dependency(conn):
    add_dependency(conn, "job_b", "job_a")
    assert list_dependencies(conn, "job_b") == ["job_a"]


def test_list_dependencies_empty_when_none(conn):
    assert list_dependencies(conn, "job_x") == []


def test_add_duplicate_dependency_is_ignored(conn):
    add_dependency(conn, "job_b", "job_a")
    add_dependency(conn, "job_b", "job_a")  # should not raise
    assert list_dependencies(conn, "job_b") == ["job_a"]


def test_self_dependency_raises(conn):
    with pytest.raises(ValueError):
        add_dependency(conn, "job_a", "job_a")


def test_remove_dependency_returns_true(conn):
    add_dependency(conn, "job_b", "job_a")
    removed = remove_dependency(conn, "job_b", "job_a")
    assert removed is True
    assert list_dependencies(conn, "job_b") == []


def test_remove_nonexistent_dependency_returns_false(conn):
    result = remove_dependency(conn, "job_b", "job_a")
    assert result is False


def test_dependents_of_returns_correct_jobs(conn):
    add_dependency(conn, "job_b", "job_a")
    add_dependency(conn, "job_c", "job_a")
    deps = dependents_of(conn, "job_a")
    assert sorted(deps) == ["job_b", "job_c"]


def test_dependencies_satisfied_no_deps(conn):
    ok, blocking = dependencies_satisfied(conn, "job_b")
    assert ok is True
    assert blocking == []


def test_dependencies_satisfied_when_dep_succeeded(conn):
    add_dependency(conn, "job_b", "job_a")
    conn.execute(
        "INSERT INTO executions (job_name, started_at, exit_code, duration) VALUES (?, ?, ?, ?)",
        ("job_a", "2024-01-01T00:00:00", 0, 1.0),
    )
    conn.commit()
    ok, blocking = dependencies_satisfied(conn, "job_b")
    assert ok is True
    assert blocking == []


def test_dependencies_not_satisfied_when_dep_failed(conn):
    add_dependency(conn, "job_b", "job_a")
    conn.execute(
        "INSERT INTO executions (job_name, started_at, exit_code, duration) VALUES (?, ?, ?, ?)",
        ("job_a", "2024-01-01T00:00:00", 1, 0.5),
    )
    conn.commit()
    ok, blocking = dependencies_satisfied(conn, "job_b")
    assert ok is False
    assert "job_a" in blocking


def test_dependencies_not_satisfied_when_dep_never_ran(conn):
    add_dependency(conn, "job_b", "job_a")
    ok, blocking = dependencies_satisfied(conn, "job_b")
    assert ok is False
    assert "job_a" in blocking
