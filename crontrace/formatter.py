"""Formatting utilities for displaying cron job execution history."""

from datetime import datetime
from typing import List, Dict, Any


STATUS_OK = "OK"
STATUS_FAIL = "FAIL"


def _format_duration(seconds: float) -> str:
    """Return a human-readable duration string."""
    if seconds < 1.0:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60.0:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.0f}s"


def _format_status(exit_code: int) -> str:
    """Return a status label based on exit code."""
    return STATUS_OK if exit_code == 0 else STATUS_FAIL


def format_row(record: Dict[str, Any]) -> str:
    """Format a single execution record as a human-readable line."""
    started = record.get("started_at", "")
    command = record.get("command", "")
    exit_code = record.get("exit_code", -1)
    duration = record.get("duration_seconds", 0.0)

    status = _format_status(exit_code)
    duration_str = _format_duration(duration)

    return f"{started}  [{status:4s}]  {duration_str:>8}  {command}"


def format_table(records: List[Dict[str, Any]], title: str = "Execution History") -> str:
    """Format a list of execution records as a plain-text table."""
    if not records:
        return f"{title}\n{'=' * len(title)}\n(no records found)\n"

    header = f"{'STARTED':<26} {'STATUS':<6} {'DURATION':>8}  COMMAND"
    separator = "-" * max(len(header), 60)

    lines = [title, "=" * len(title), header, separator]
    for record in records:
        lines.append(format_row(record))
    lines.append(separator)
    lines.append(f"{len(records)} record(s) shown.")
    return "\n".join(lines) + "\n"
