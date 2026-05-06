"""Tests for crontrace.diff_reporter."""
import pytest
from crontrace.diff_reporter import diff_executions, render_diff


def _exec(
    exit_code=0,
    duration=1.5,
    stdout="ok",
    stderr="",
    started_at="2024-01-01T00:00:00",
):
    return {
        "exit_code": exit_code,
        "duration": duration,
        "stdout": stdout,
        "stderr": stderr,
        "started_at": started_at,
    }


# --- diff_executions ---

def test_diff_identical_records_returns_empty():
    rec = _exec()
    assert diff_executions(rec, rec) == {}


def test_diff_detects_exit_code_change():
    old = _exec(exit_code=0)
    new = _exec(exit_code=1)
    changes = diff_executions(old, new)
    assert "exit_code" in changes
    assert changes["exit_code"] == {"old": 0, "new": 1}


def test_diff_detects_duration_change():
    old = _exec(duration=1.0)
    new = _exec(duration=3.5)
    changes = diff_executions(old, new)
    assert "duration" in changes
    assert changes["duration"]["old"] == pytest.approx(1.0)
    assert changes["duration"]["new"] == pytest.approx(3.5)


def test_diff_detects_stdout_change():
    old = _exec(stdout="hello")
    new = _exec(stdout="world")
    changes = diff_executions(old, new)
    assert "stdout" in changes


def test_diff_multiple_fields_changed():
    old = _exec(exit_code=0, stderr="")
    new = _exec(exit_code=2, stderr="error!")
    changes = diff_executions(old, new)
    assert "exit_code" in changes
    assert "stderr" in changes


def test_diff_ignores_started_at():
    old = _exec(started_at="2024-01-01T00:00:00")
    new = _exec(started_at="2024-06-01T12:00:00")
    # started_at is not in _COMPARE_KEYS
    changes = diff_executions(old, new)
    assert "started_at" not in changes


# --- render_diff ---

def test_render_diff_no_changes_message():
    rec = _exec()
    result = render_diff("backup", rec, rec)
    assert "No changes" in result
    assert "backup" in result


def test_render_diff_contains_job_name():
    old = _exec(exit_code=0)
    new = _exec(exit_code=1)
    result = render_diff("myjob", old, new)
    assert "myjob" in result


def test_render_diff_shows_ok_to_fail():
    old = _exec(exit_code=0)
    new = _exec(exit_code=1)
    result = render_diff("myjob", old, new)
    assert "OK" in result
    assert "FAIL" in result


def test_render_diff_shows_duration():
    old = _exec(duration=0.5)
    new = _exec(duration=9.9)
    result = render_diff("myjob", old, new)
    assert "0.50s" in result
    assert "9.90s" in result


def test_render_diff_truncates_long_stdout():
    old = _exec(stdout="a" * 80)
    new = _exec(stdout="b" * 80)
    result = render_diff("myjob", old, new)
    # Should contain ellipsis for truncated values
    assert "…" in result
