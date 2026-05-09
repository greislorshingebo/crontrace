"""Tests for crontrace.job_hooks and crontrace.hook_reporter."""

import sqlite3
import pytest

from crontrace.job_hooks import (
    set_hook,
    get_hook,
    delete_hook,
    list_hooks,
)
from crontrace.hook_reporter import render_hook_row, render_hook_table


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


# --- job_hooks ---

def test_get_hook_returns_none_when_missing(conn):
    assert get_hook(conn, "backup", "pre") is None


def test_set_and_get_hook_round_trip(conn):
    set_hook(conn, "backup", "pre", "echo starting")
    hook = get_hook(conn, "backup", "pre")
    assert hook is not None
    assert hook["job_name"] == "backup"
    assert hook["hook_type"] == "pre"
    assert hook["command"] == "echo starting"
    assert hook["enabled"] is True


def test_set_hook_disabled(conn):
    set_hook(conn, "backup", "post", "notify.sh", enabled=False)
    hook = get_hook(conn, "backup", "post")
    assert hook["enabled"] is False


def test_set_hook_overwrites_existing(conn):
    set_hook(conn, "sync", "pre", "old_cmd.sh")
    set_hook(conn, "sync", "pre", "new_cmd.sh")
    hook = get_hook(conn, "sync", "pre")
    assert hook["command"] == "new_cmd.sh"


def test_set_hook_invalid_type_raises(conn):
    with pytest.raises(ValueError):
        set_hook(conn, "backup", "during", "echo hi")


def test_delete_hook_removes_entry(conn):
    set_hook(conn, "backup", "pre", "echo start")
    delete_hook(conn, "backup", "pre")
    assert get_hook(conn, "backup", "pre") is None


def test_delete_hook_nonexistent_is_safe(conn):
    delete_hook(conn, "ghost", "post")  # should not raise


def test_list_hooks_empty_when_none(conn):
    assert list_hooks(conn, "backup") == []


def test_list_hooks_returns_both_types(conn):
    set_hook(conn, "deploy", "pre", "pre.sh")
    set_hook(conn, "deploy", "post", "post.sh")
    hooks = list_hooks(conn, "deploy")
    types = [h["hook_type"] for h in hooks]
    assert "pre" in types
    assert "post" in types


def test_list_hooks_independent_per_job(conn):
    set_hook(conn, "jobA", "pre", "a.sh")
    set_hook(conn, "jobB", "pre", "b.sh")
    assert len(list_hooks(conn, "jobA")) == 1
    assert list_hooks(conn, "jobA")[0]["command"] == "a.sh"


# --- hook_reporter ---

def test_render_hook_row_contains_hook_type():
    hook = {"job_name": "backup", "hook_type": "pre", "command": "echo hi", "enabled": True}
    assert "PRE" in render_hook_row(hook)


def test_render_hook_row_contains_command():
    hook = {"job_name": "backup", "hook_type": "post", "command": "notify.sh", "enabled": True}
    assert "notify.sh" in render_hook_row(hook)


def test_render_hook_row_shows_off_when_disabled():
    hook = {"job_name": "x", "hook_type": "pre", "command": "cmd", "enabled": False}
    assert "OFF" in render_hook_row(hook)


def test_render_hook_table_shows_job_name():
    result = render_hook_table("myjob", [])
    assert "myjob" in result


def test_render_hook_table_empty_shows_placeholder():
    result = render_hook_table("myjob", [])
    assert "no hooks" in result


def test_render_hook_table_with_hooks_contains_command():
    hooks = [{"job_name": "x", "hook_type": "pre", "command": "run.sh", "enabled": True}]
    result = render_hook_table("x", hooks)
    assert "run.sh" in result
