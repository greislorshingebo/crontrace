"""Tests for crontrace.job_env and crontrace.env_reporter."""

import json
import sqlite3

import pytest

from crontrace.job_env import (
    clear_env,
    delete_env_key,
    export_env_json,
    get_env,
    set_env,
    set_env_bulk,
)
from crontrace.env_reporter import render_env_row, render_env_table


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# job_env
# ---------------------------------------------------------------------------

def test_get_env_empty_when_no_vars(conn):
    assert get_env(conn, "myjob") == {}


def test_set_and_get_round_trip(conn):
    set_env(conn, "myjob", "FOO", "bar")
    assert get_env(conn, "myjob") == {"FOO": "bar"}


def test_set_env_overwrites_existing(conn):
    set_env(conn, "myjob", "FOO", "bar")
    set_env(conn, "myjob", "FOO", "baz")
    assert get_env(conn, "myjob")["FOO"] == "baz"


def test_set_env_bulk_stores_all_keys(conn):
    env = {"A": "1", "B": "2", "C": "3"}
    set_env_bulk(conn, "myjob", env)
    assert get_env(conn, "myjob") == env


def test_set_env_bulk_replaces_previous(conn):
    set_env(conn, "myjob", "OLD", "value")
    set_env_bulk(conn, "myjob", {"NEW": "val"})
    result = get_env(conn, "myjob")
    assert "OLD" not in result
    assert result["NEW"] == "val"


def test_delete_env_key_removes_key(conn):
    set_env(conn, "myjob", "FOO", "bar")
    deleted = delete_env_key(conn, "myjob", "FOO")
    assert deleted is True
    assert "FOO" not in get_env(conn, "myjob")


def test_delete_env_key_returns_false_when_missing(conn):
    result = delete_env_key(conn, "myjob", "NOPE")
    assert result is False


def test_clear_env_removes_all_vars(conn):
    set_env_bulk(conn, "myjob", {"A": "1", "B": "2"})
    count = clear_env(conn, "myjob")
    assert count == 2
    assert get_env(conn, "myjob") == {}


def test_env_vars_are_independent_per_job(conn):
    set_env(conn, "job_a", "KEY", "alpha")
    set_env(conn, "job_b", "KEY", "beta")
    assert get_env(conn, "job_a")["KEY"] == "alpha"
    assert get_env(conn, "job_b")["KEY"] == "beta"


def test_export_env_json_returns_valid_json(conn):
    set_env_bulk(conn, "myjob", {"X": "1", "Y": "2"})
    raw = export_env_json(conn, "myjob")
    parsed = json.loads(raw)
    assert parsed == {"X": "1", "Y": "2"}


def test_export_env_json_empty(conn):
    raw = export_env_json(conn, "ghost")
    assert json.loads(raw) == {}


# ---------------------------------------------------------------------------
# env_reporter
# ---------------------------------------------------------------------------

def test_render_env_row_contains_key_and_value():
    row = render_env_row("MY_VAR", "hello")
    assert "MY_VAR" in row
    assert "hello" in row


def test_render_env_table_contains_job_name():
    table = render_env_table("backup_job", {"PATH": "/usr/bin"})
    assert "backup_job" in table


def test_render_env_table_contains_key_and_value():
    table = render_env_table("myjob", {"TOKEN": "secret"})
    assert "TOKEN" in table
    assert "secret" in table


def test_render_env_table_empty_message(conn):
    table = render_env_table("emptyjob", {})
    assert "no variables" in table


def test_render_env_row_truncates_long_value():
    long_val = "x" * 100
    row = render_env_row("KEY", long_val)
    assert "…" in row
