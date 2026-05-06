"""schedule_runner.py – checks due schedules and dispatches cron jobs."""

from __future__ import annotations

import datetime
from typing import List, Tuple

from crontrace.schedule_store import list_schedules, fetch_schedule
from crontrace.scheduler import prev_run, next_run
from crontrace.runner import run_job


def _utcnow() -> datetime.datetime:
    """Return current UTC time (naive)."""
    return datetime.datetime.utcnow()


def find_due_jobs(
    db_path: str,
    now: datetime.datetime | None = None,
) -> List[str]:
    """Return job names whose next scheduled run is <= *now*.

    A job is considered due when the *prev_run* calculated from *now* is
    within the same minute as *now* (i.e. the schedule fired this minute).
    """
    if now is None:
        now = _utcnow()

    schedules = list_schedules(db_path)
    due: List[str] = []

    for job_name, expression in schedules:
        try:
            prev = prev_run(expression, now)
        except Exception:
            continue
        # Due when the previous fire-time is within the current minute
        delta = now - prev
        if delta.total_seconds() < 60:
            due.append(job_name)

    return due


def run_due_jobs(
    db_path: str,
    now: datetime.datetime | None = None,
) -> List[Tuple[str, int]]:
    """Find and execute all due jobs.

    Returns a list of (job_name, exit_code) tuples for every job that was
    dispatched.
    """
    if now is None:
        now = _utcnow()

    due = find_due_jobs(db_path, now=now)
    results: List[Tuple[str, int]] = []

    for job_name in due:
        row = fetch_schedule(db_path, job_name)
        if row is None:
            continue
        _, _, command = row  # (job_name, expression, command)
        exit_code = run_job(job_name, command, db_path)
        results.append((job_name, exit_code))

    return results
