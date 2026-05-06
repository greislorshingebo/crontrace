"""Tests for crontrace.report."""

from crontrace.report import render_summary


def _row(exit_code: int, duration: float, idx: int = 1):
    return (idx, "backupjob", "2024-06-01T12:00:00", duration, exit_code, "", "")


def test_render_summary_contains_job_name():
    rows = [_row(0, 3.0)]
    output = render_summary("backupjob", rows)
    assert "backupjob" in output


def test_render_summary_shows_ok_status():
    rows = [_row(0, 1.0)]
    output = render_summary("myjob", rows)
    assert "OK" in output


def test_render_summary_shows_fail_status():
    rows = [_row(1, 1.0)]
    output = render_summary("myjob", rows)
    assert "FAIL" in output


def test_render_summary_empty_rows():
    output = render_summary("emptyjob", [])
    assert "emptyjob" in output
    assert "n/a" in output


def test_render_summary_duration_seconds():
    rows = [_row(0, 45.5)]
    output = render_summary("myjob", rows)
    assert "45.50s" in output


def test_render_summary_duration_minutes():
    rows = [_row(0, 125.0)]
    output = render_summary("myjob", rows)
    assert "2m" in output


def test_render_summary_success_rate_percentage():
    rows = [_row(0, 1.0, 1), _row(0, 1.0, 2), _row(1, 1.0, 3)]
    output = render_summary("myjob", rows)
    assert "66.7%" in output


def test_render_summary_multiline():
    rows = [_row(0, 2.0)]
    output = render_summary("myjob", rows)
    assert len(output.splitlines()) > 5
