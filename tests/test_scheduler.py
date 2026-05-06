"""Tests for crontrace.scheduler."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from crontrace.scheduler import (
    is_valid_expression,
    next_run,
    prev_run,
    describe_schedule,
)

# ---------------------------------------------------------------------------
# is_valid_expression
# ---------------------------------------------------------------------------

def test_valid_expression_returns_true():
    assert is_valid_expression("0 * * * *") is True


def test_every_minute_is_valid():
    assert is_valid_expression("* * * * *") is True


def test_invalid_expression_returns_false():
    assert is_valid_expression("not a cron") is False


def test_too_few_fields_is_invalid():
    assert is_valid_expression("0 * *") is False


# ---------------------------------------------------------------------------
# next_run
# ---------------------------------------------------------------------------

def test_next_run_is_after_base():
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = next_run("0 * * * *", base=base)
    assert result > base


def test_next_run_returns_datetime_with_timezone():
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = next_run("*/5 * * * *", base=base)
    assert result.tzinfo is not None


def test_next_run_raises_on_invalid_expression():
    with pytest.raises(ValueError, match="Invalid cron expression"):
        next_run("bad expr")


# ---------------------------------------------------------------------------
# prev_run
# ---------------------------------------------------------------------------

def test_prev_run_is_before_base():
    base = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
    result = prev_run("0 * * * *", base=base)
    assert result < base


def test_prev_run_raises_on_invalid_expression():
    with pytest.raises(ValueError):
        prev_run("bad expr")


# ---------------------------------------------------------------------------
# describe_schedule
# ---------------------------------------------------------------------------

def test_describe_schedule_returns_n_items():
    items = describe_schedule("0 9 * * 1", n=4)
    assert len(items) == 4


def test_describe_schedule_items_are_iso_strings():
    items = describe_schedule("0 0 * * *", n=2)
    for item in items:
        # basic sanity: parseable as a datetime
        datetime.strptime(item, "%Y-%m-%dT%H:%M:%SZ")


def test_describe_schedule_raises_on_invalid():
    with pytest.raises(ValueError):
        describe_schedule("not valid")
