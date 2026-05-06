"""Tests for crontrace.dashboard."""

from __future__ import annotations

import pytest

from crontrace.dashboard import render_job_panel, render_dashboard


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _row(job: str, exit_code: int, duration: float, started_at: str = "2024-01-01T00:00:00"):
    return {
        "job_name": job,
        "started_at": started_at,
        "duration": duration,
        "exit_code": exit_code,
    }


# ---------------------------------------------------------------------------
# render_job_panel
# ---------------------------------------------------------------------------

def test_render_job_panel_contains_job_name():
    rows = [_row("backup", 0, 10.0)]
    result = render_job_panel("backup", rows)
    assert "backup" in result


def test_render_job_panel_shows_ok_when_no_failures():
    rows = [_row("backup", 0, 10.0), _row("backup", 0, 12.0)]
    result = render_job_panel("backup", rows)
    assert "OK" in result or "ok" in result.lower()


def test_render_job_panel_shows_alert_on_high_failure_rate():
    rows = [_row("sync", 1, 5.0), _row("sync", 1, 5.0), _row("sync", 0, 5.0)]
    result = render_job_panel("sync", rows, failure_rate_threshold=0.3)
    assert "failure_rate" in result or "failure" in result.lower()


def test_render_job_panel_no_alerts_section_when_clean():
    rows = [_row("clean", 0, 1.0)]
    result = render_job_panel("clean", rows, failure_rate_threshold=1.0, avg_duration_threshold=9999)
    assert "Alerts" not in result


def test_render_job_panel_shows_alert_on_slow_duration():
    rows = [_row("etl", 0, 600.0), _row("etl", 0, 700.0)]
    result = render_job_panel("etl", rows, avg_duration_threshold=100.0)
    assert "duration" in result.lower() or "Alerts" in result


# ---------------------------------------------------------------------------
# render_dashboard
# ---------------------------------------------------------------------------

def test_render_dashboard_empty_returns_message():
    result = render_dashboard([])
    assert "No jobs" in result


def test_render_dashboard_contains_all_job_names():
    jobs = [
        ("backup", [_row("backup", 0, 5.0)]),
        ("sync", [_row("sync", 1, 3.0)]),
    ]
    result = render_dashboard(jobs)
    assert "backup" in result
    assert "sync" in result


def test_render_dashboard_single_job():
    jobs = [("solo", [_row("solo", 0, 2.0)])]
    result = render_dashboard(jobs)
    assert "solo" in result


def test_render_dashboard_separates_jobs():
    jobs = [
        ("job_a", [_row("job_a", 0, 1.0)]),
        ("job_b", [_row("job_b", 0, 2.0)]),
    ]
    result = render_dashboard(jobs)
    # Both job names must appear and be distinct sections
    assert result.index("job_a") < result.index("job_b")
