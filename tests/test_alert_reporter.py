"""Tests for crontrace.alert_reporter."""

import pytest

from crontrace.alert_reporter import render_alert, render_alerts, print_alerts


_FR_ALERT = {
    "type": "failure_rate",
    "value": 0.6,
    "threshold": 0.5,
    "message": "Failure rate 60.0% exceeds threshold 50.0%",
}

_DUR_ALERT = {
    "type": "avg_duration",
    "value": 350.0,
    "threshold": 300.0,
    "message": "Average duration 350.0s exceeds threshold 300.0s",
}


def test_render_alert_failure_rate_contains_type():
    line = render_alert(_FR_ALERT)
    assert "failure_rate" in line


def test_render_alert_contains_message():
    line = render_alert(_FR_ALERT)
    assert _FR_ALERT["message"] in line


def test_render_alert_duration_contains_type():
    line = render_alert(_DUR_ALERT)
    assert "avg_duration" in line


def test_render_alerts_empty_returns_empty_string():
    assert render_alerts([]) == ""


def test_render_alerts_contains_job_name():
    text = render_alerts([_FR_ALERT], job_name="backup")
    assert "backup" in text


def test_render_alerts_contains_all_alert_messages():
    text = render_alerts([_FR_ALERT, _DUR_ALERT], job_name="sync")
    assert _FR_ALERT["message"] in text
    assert _DUR_ALERT["message"] in text


def test_render_alerts_no_job_name_still_renders():
    text = render_alerts([_FR_ALERT])
    assert "ALERT" in text


def test_print_alerts_empty_prints_nothing(capsys):
    print_alerts([])
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_alerts_nonempty_prints_something(capsys):
    print_alerts([_FR_ALERT], job_name="myjob")
    captured = capsys.readouterr()
    assert "myjob" in captured.out
    assert "failure_rate" in captured.out
