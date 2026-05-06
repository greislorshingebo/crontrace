"""Tests for crontrace.summarizer."""

import pytest
from crontrace.summarizer import summarize, _safe_avg


def _row(exit_code: int, duration: float, idx: int = 1):
    """Build a minimal fake row tuple."""
    return (idx, "myjob", "2024-01-01T00:00:00", duration, exit_code, "", "")


def test_safe_avg_empty():
    assert _safe_avg([]) is None


def test_safe_avg_values():
    assert _safe_avg([1.0, 3.0]) == pytest.approx(2.0)


def test_summarize_empty_rows():
    result = summarize([])
    assert result["total"] == 0
    assert result["successes"] == 0
    assert result["failures"] == 0
    assert result["success_rate"] is None
    assert result["avg_duration"] is None
    assert result["min_duration"] is None
    assert result["max_duration"] is None
    assert result["last_exit"] is None


def test_summarize_all_success():
    rows = [_row(0, 1.0, i) for i in range(5)]
    result = summarize(rows)
    assert result["total"] == 5
    assert result["successes"] == 5
    assert result["failures"] == 0
    assert result["success_rate"] == pytest.approx(1.0)


def test_summarize_mixed():
    rows = [_row(0, 2.0, 1), _row(1, 4.0, 2), _row(0, 6.0, 3)]
    result = summarize(rows)
    assert result["total"] == 3
    assert result["successes"] == 2
    assert result["failures"] == 1
    assert result["success_rate"] == pytest.approx(2 / 3)


def test_summarize_duration_stats():
    rows = [_row(0, 10.0, 1), _row(0, 20.0, 2), _row(0, 30.0, 3)]
    result = summarize(rows)
    assert result["avg_duration"] == pytest.approx(20.0)
    assert result["min_duration"] == pytest.approx(10.0)
    assert result["max_duration"] == pytest.approx(30.0)


def test_summarize_last_exit_is_last_row():
    rows = [_row(0, 1.0, 1), _row(2, 1.0, 2)]
    result = summarize(rows)
    assert result["last_exit"] == 2


def test_summarize_single_row_failure():
    rows = [_row(127, 5.5, 1)]
    result = summarize(rows)
    assert result["failures"] == 1
    assert result["success_rate"] == pytest.approx(0.0)
    assert result["last_exit"] == 127
