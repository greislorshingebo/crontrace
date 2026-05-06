"""Render alert results as human-readable text for CLI output or log files."""

from __future__ import annotations

from typing import Sequence

_ICON = {"failure_rate": "\u26a0\ufe0f ", "avg_duration": "\u23f0 "}


def _icon(alert_type: str) -> str:
    return _ICON.get(alert_type, "!! ")


def render_alert(alert: dict) -> str:
    """Format a single alert dict as a one-line string."""
    icon = _icon(alert["type"])
    return f"{icon}ALERT [{alert['type']}]: {alert['message']}"


def render_alerts(alerts: Sequence[dict], job_name: str = "") -> str:
    """Return a multi-line block summarising all alerts for *job_name*.

    Returns an empty string when *alerts* is empty.
    """
    if not alerts:
        return ""

    header = f"--- Alerts for '{job_name}' ---" if job_name else "--- Alerts ---"
    lines = [header]
    for alert in alerts:
        lines.append(render_alert(alert))
    lines.append("-" * len(header))
    return "\n".join(lines)


def print_alerts(alerts: Sequence[dict], job_name: str = "") -> None:
    """Print alert block to stdout; does nothing when list is empty."""
    text = render_alerts(alerts, job_name)
    if text:
        print(text)
