"""Tests for crontrace.job_metrics."""

from __future__ import annotations

import pytest

from crontrace.job_metrics import (
    compute_metrics,
    duration_percentile,
    median_duration,
    run_count,
    success_rate,
)


def _row(exit_code: int, duration: float) -> tuple:
    """Minimal fake storage row: (id, job, started_at, exit_code, duration, stdout, stderr)."""
    return (1, "myjob", "2024-01-01T00:00:00", exit_code, duration, "", "")


# ---------------------------------------------------------------------------
# success_rate
# ---------------------------------------------------------------------------

def test_success_rate_empty_returns_zero():
    assert success_rate([]) == 0.0


def test_success_rate_all_ok():
    rows = [_row(0, 1.0), _row(0, 2.0)]
    assert success_rate(rows) == 1.0


def test_success_rate_all_fail():
    rows = [_row(1, 1.0), _row(2, 1.0)]
    assert success_rate(rows) == 0.0


def test_success_rate_mixed():
    rows = [_row(0, 1.0), _row(1, 1.0), _row(0, 1.0), _row(0, 1.0)]
    assert success_rate(rows) == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# run_count
# ---------------------------------------------------------------------------

def test_run_count_empty():
    assert run_count([]) == 0


def test_run_count_returns_length():
    rows = [_row(0, 1.0)] * 7
    assert run_count(rows) == 7


# ---------------------------------------------------------------------------
# duration_percentile / median_duration
# ---------------------------------------------------------------------------

def test_duration_percentile_empty_returns_none():
    assert duration_percentile([], 50) is None


def test_duration_percentile_p0_is_min():
    rows = [_row(0, 3.0), _row(0, 1.0), _row(0, 2.0)]
    assert duration_percentile(rows, 0) == pytest.approx(1.0)


def test_duration_percentile_p100_is_max():
    rows = [_row(0, 3.0), _row(0, 1.0), _row(0, 2.0)]
    assert duration_percentile(rows, 100) == pytest.approx(3.0)


def test_median_duration_odd_count():
    rows = [_row(0, 1.0), _row(0, 3.0), _row(0, 5.0)]
    assert median_duration(rows) == pytest.approx(3.0)


def test_median_duration_even_count():
    rows = [_row(0, 1.0), _row(0, 2.0), _row(0, 3.0), _row(0, 4.0)]
    assert median_duration(rows) == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# compute_metrics
# ---------------------------------------------------------------------------

def test_compute_metrics_empty_rows():
    result = compute_metrics("backup", [])
    assert result["job"] == "backup"
    assert result["run_count"] == 0
    assert result["success_rate"] == 0.0
    assert result["median_duration"] is None
    assert result["p95_duration"] is None


def test_compute_metrics_keys_present():
    rows = [_row(0, 2.5), _row(1, 1.0), _row(0, 3.0)]
    result = compute_metrics("sync", rows)
    expected_keys = {"job", "run_count", "success_rate", "median_duration", "p95_duration", "min_duration", "max_duration"}
    assert expected_keys == set(result.keys())


def test_compute_metrics_min_max():
    rows = [_row(0, 1.0), _row(0, 5.0), _row(0, 3.0)]
    result = compute_metrics("job", rows)
    assert result["min_duration"] == pytest.approx(1.0)
    assert result["max_duration"] == pytest.approx(5.0)
