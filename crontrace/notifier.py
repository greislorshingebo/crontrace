"""Alert/notification module for crontrace.

Sends notifications when a cron job fails (non-zero exit code).
Currently supports stdout (print) and webhook (HTTP POST) channels.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Optional


def _build_payload(job_name: str, exit_code: int, duration: float, started_at: str) -> dict:
    """Build a notification payload dict."""
    return {
        "job": job_name,
        "exit_code": exit_code,
        "duration_seconds": round(duration, 3),
        "started_at": started_at,
        "status": "FAIL" if exit_code != 0 else "OK",
    }


def notify_stdout(job_name: str, exit_code: int, duration: float, started_at: str) -> None:
    """Print a notification message to stdout."""
    payload = _build_payload(job_name, exit_code, duration, started_at)
    status = payload["status"]
    print(
        f"[crontrace] {status} | job={job_name!r} "
        f"exit={exit_code} duration={payload['duration_seconds']}s "
        f"started={started_at}"
    )


def notify_webhook(
    url: str,
    job_name: str,
    exit_code: int,
    duration: float,
    started_at: str,
    timeout: int = 5,
) -> bool:
    """POST a JSON notification to a webhook URL.

    Returns True on success, False on any network/HTTP error.
    """
    payload = _build_payload(job_name, exit_code, duration, started_at)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def dispatch(
    job_name: str,
    exit_code: int,
    duration: float,
    started_at: str,
    webhook_url: Optional[str] = None,
    only_on_failure: bool = True,
) -> None:
    """Dispatch notifications via all configured channels.

    If *only_on_failure* is True (default) notifications are suppressed
    when exit_code == 0.
    """
    if only_on_failure and exit_code == 0:
        return

    notify_stdout(job_name, exit_code, duration, started_at)

    if webhook_url:
        notify_webhook(webhook_url, job_name, exit_code, duration, started_at)
