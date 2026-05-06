"""Tests for crontrace.alerting."""

import pytest
from unittest.mock import MagicMock

from crontrace.alerting import (
    _failure_rate,
    _avg_duration,
    check_failure_rate,
    check_avg_duration,
    evaluate_alerts,
    DEFAULT_FAILURE_RATE_THRESHOLD,
    DEFAULT_DURATION_THRESHOLD_S,
)


def _row(exit_code: int, duration_s: float):
    m = MagicMock()
    m.__getitem__ = lambda self, k: {"exit_code": exit_code, "duration_s": duration_s}[k]
    return m


# --- _failure_rate ---

def test_failure_rate_empty():
    assert _failure_rate([]) == 0.0


def test_failure_rate_all_success():
    rows = [_row(0, 1.0), _row(0, 2.0)]
    assert _failure_rate(rows) == 0.0


def test_failure_rate_all_fail():
    rows = [_row(1, 1.0), _row(2, 1.0)]
    assert _failure_rate(rows) == 1.0


def test_failure_rate_mixed():
    rows = [_row(0, 1.0), _row(1, 1.0), _row(0, 1.0), _row(1, 1.0)]
    assert _failure_rate(rows) == 0.5


# --- _avg_duration ---

def test_avg_duration_empty():
    assert _avg_duration([]) == 0.0


def test_avg_duration_values():
    rows = [_row(0, 10.0), _row(0, 20.0), _row(0, 30.0)]
    assert _avg_duration(rows) == 20.0


# --- check_failure_rate ---

def test_check_failure_rate_below_threshold_returns_none():
    rows = [_row(0, 1.0), _row(0, 1.0), _row(1, 1.0)]  # 33 %
    assert check_failure_rate(rows, threshold=0.5) is None


def test_check_failure_rate_above_threshold_returns_dict():
    rows = [_row(1, 1.0), _row(1, 1.0), _row(0, 1.0)]  # 66 %
    result = check_failure_rate(rows, threshold=0.5)
    assert result is not None
    assert result["type"] == "failure_rate"
    assert "message" in result


# --- check_avg_duration ---

def test_check_avg_duration_below_threshold_returns_none():
    rows = [_row(0, 10.0), _row(0, 20.0)]
    assert check_avg_duration(rows, threshold=300.0) is None


def test_check_avg_duration_above_threshold_returns_dict():
    rows = [_row(0, 400.0), _row(0, 500.0)]
    result = check_avg_duration(rows, threshold=300.0)
    assert result is not None
    assert result["type"] == "avg_duration"
    assert result["value"] == 450.0


# --- evaluate_alerts ---

def test_evaluate_alerts_no_alerts_for_healthy_job():
    rows = [_row(0, 5.0)] * 10
    alerts = evaluate_alerts(rows)
    assert alerts == []


def test_evaluate_alerts_returns_both_alerts():
    rows = [_row(1, 400.0)] * 10
    alerts = evaluate_alerts(rows, failure_rate_threshold=0.3, duration_threshold_s=300.0)
    types = {a["type"] for a in alerts}
    assert "failure_rate" in types
    assert "avg_duration" in types


def test_evaluate_alerts_empty_rows_no_alerts():
    assert evaluate_alerts([]) == []
