"""Tests for crontrace.tagging."""

from __future__ import annotations

import sqlite3
import pytest

from crontrace.tagging import (
    add_tag,
    remove_tag,
    list_tags,
    jobs_by_tag,
    clear_tags,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_add_and_list_tags(conn):
    add_tag(conn, "backup", "critical")
    add_tag(conn, "backup", "nightly")
    tags = list_tags(conn, "backup")
    assert "critical" in tags
    assert "nightly" in tags


def test_list_tags_empty_when_no_tags(conn):
    assert list_tags(conn, "nonexistent") == []


def test_add_tag_is_case_normalised(conn):
    add_tag(conn, "sync", "PROD")
    assert list_tags(conn, "sync") == ["prod"]


def test_add_tag_duplicate_is_ignored(conn):
    add_tag(conn, "deploy", "important")
    add_tag(conn, "deploy", "important")  # duplicate — should not raise
    assert list_tags(conn, "deploy").count("important") == 1


def test_remove_tag(conn):
    add_tag(conn, "cleanup", "weekly")
    remove_tag(conn, "cleanup", "weekly")
    assert list_tags(conn, "cleanup") == []


def test_remove_tag_noop_when_missing(conn):
    remove_tag(conn, "ghost", "phantom")  # must not raise


def test_jobs_by_tag_returns_matching_jobs(conn):
    add_tag(conn, "job_a", "prod")
    add_tag(conn, "job_b", "prod")
    add_tag(conn, "job_c", "staging")
    jobs = jobs_by_tag(conn, "prod")
    assert "job_a" in jobs
    assert "job_b" in jobs
    assert "job_c" not in jobs


def test_jobs_by_tag_empty_when_no_match(conn):
    assert jobs_by_tag(conn, "unknown") == []


def test_clear_tags_removes_all(conn):
    add_tag(conn, "report", "daily")
    add_tag(conn, "report", "finance")
    clear_tags(conn, "report")
    assert list_tags(conn, "report") == []


def test_clear_tags_does_not_affect_other_jobs(conn):
    add_tag(conn, "job_x", "keep")
    add_tag(conn, "job_y", "keep")
    clear_tags(conn, "job_x")
    assert list_tags(conn, "job_y") == ["keep"]
