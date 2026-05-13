"""Tests for crontrace.job_ownership."""

import sqlite3
import pytest

from crontrace.job_ownership import (
    set_ownership,
    get_ownership,
    delete_ownership,
    list_ownership,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_ownership_returns_none_when_missing(conn):
    assert get_ownership(conn, "my_job") is None


def test_set_and_get_round_trip(conn):
    set_ownership(conn, "my_job", owner="alice", team="platform", contact="alice@example.com")
    result = get_ownership(conn, "my_job")
    assert result is not None
    assert result["job_name"] == "my_job"
    assert result["owner"] == "alice"
    assert result["team"] == "platform"
    assert result["contact"] == "alice@example.com"


def test_set_ownership_overwrites_existing(conn):
    set_ownership(conn, "my_job", owner="alice", team="platform")
    set_ownership(conn, "my_job", owner="bob", team="ops")
    result = get_ownership(conn, "my_job")
    assert result["owner"] == "bob"
    assert result["team"] == "ops"


def test_set_ownership_strips_whitespace(conn):
    set_ownership(conn, "my_job", owner="  alice  ", team=" platform ", contact=" a@b.com ")
    result = get_ownership(conn, "my_job")
    assert result["owner"] == "alice"
    assert result["team"] == "platform"
    assert result["contact"] == "a@b.com"


def test_set_ownership_partial_fields_default_empty(conn):
    set_ownership(conn, "my_job", owner="alice")
    result = get_ownership(conn, "my_job")
    assert result["team"] == ""
    assert result["contact"] == ""


def test_delete_ownership_returns_true_when_exists(conn):
    set_ownership(conn, "my_job", owner="alice")
    assert delete_ownership(conn, "my_job") is True


def test_delete_ownership_returns_false_when_missing(conn):
    assert delete_ownership(conn, "nonexistent") is False


def test_delete_ownership_removes_record(conn):
    set_ownership(conn, "my_job", owner="alice")
    delete_ownership(conn, "my_job")
    assert get_ownership(conn, "my_job") is None


def test_list_ownership_empty_returns_empty_list(conn):
    assert list_ownership(conn) == []


def test_list_ownership_returns_all_entries(conn):
    set_ownership(conn, "job_b", owner="bob")
    set_ownership(conn, "job_a", owner="alice")
    results = list_ownership(conn)
    assert len(results) == 2
    # ordered by job_name
    assert results[0]["job_name"] == "job_a"
    assert results[1]["job_name"] == "job_b"


def test_updated_at_is_populated(conn):
    set_ownership(conn, "my_job", owner="alice")
    result = get_ownership(conn, "my_job")
    assert result["updated_at"] != ""
    assert "T" in result["updated_at"]


def test_independent_records_per_job(conn):
    set_ownership(conn, "job_a", owner="alice", team="alpha")
    set_ownership(conn, "job_b", owner="bob", team="beta")
    a = get_ownership(conn, "job_a")
    b = get_ownership(conn, "job_b")
    assert a["owner"] == "alice"
    assert b["owner"] == "bob"
