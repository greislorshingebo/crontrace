"""Utilities for parsing and validating cron expressions attached to jobs."""

from __future__ import annotations

from croniter import croniter
from datetime import datetime, timezone
from typing import Optional


def is_valid_expression(expression: str) -> bool:
    """Return True if *expression* is a valid 5-field cron expression."""
    return croniter.is_valid(expression)


def next_run(expression: str, base: Optional[datetime] = None) -> datetime:
    """Return the next scheduled UTC datetime after *base*.

    Parameters
    ----------
    expression:
        A valid 5-field cron expression, e.g. ``"0 * * * *"``.
    base:
        The reference point in time.  Defaults to *now* in UTC.

    Raises
    ------
    ValueError
        If *expression* is not a valid cron expression.
    """
    if not is_valid_expression(expression):
        raise ValueError(f"Invalid cron expression: {expression!r}")

    if base is None:
        base = datetime.now(tz=timezone.utc)

    itr = croniter(expression, base)
    dt: datetime = itr.get_next(datetime)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def prev_run(expression: str, base: Optional[datetime] = None) -> datetime:
    """Return the most recent scheduled UTC datetime before *base*."""
    if not is_valid_expression(expression):
        raise ValueError(f"Invalid cron expression: {expression!r}")

    if base is None:
        base = datetime.now(tz=timezone.utc)

    itr = croniter(expression, base)
    dt: datetime = itr.get_prev(datetime)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def describe_schedule(expression: str, n: int = 3) -> list[str]:
    """Return the next *n* ISO-formatted UTC run times for *expression*."""
    if not is_valid_expression(expression):
        raise ValueError(f"Invalid cron expression: {expression!r}")

    base = datetime.now(tz=timezone.utc)
    itr = croniter(expression, base)
    return [
        itr.get_next(datetime).strftime("%Y-%m-%dT%H:%M:%SZ")
        for _ in range(n)
    ]
