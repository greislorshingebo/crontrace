"""Render job priority information as plain-text tables."""

from typing import List

_PRIORITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "normal": "🟡",
    "low": "⚪",
}

_COL_JOB = 30
_COL_PRI = 10


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def render_priority_row(entry: dict) -> str:
    """Format a single priority row for display."""
    job = _truncate(entry.get("job_name", ""), _COL_JOB)
    pri = entry.get("priority", "normal")
    icon = _PRIORITY_ICONS.get(pri, "")
    updated = entry.get("updated_at", "")[:19]
    return f"{job:<{_COL_JOB}}  {icon} {pri:<{_COL_PRI}}  {updated}"


def render_priority_table(entries: List[dict], job_name: str = "") -> str:
    """Render a full table of priority entries."""
    header_job = "JOB"
    header = (
        f"{header_job:<{_COL_JOB}}  {'PRIORITY':<{_COL_PRI + 3}}  UPDATED AT"
    )
    sep = "-" * len(header)
    lines = [header, sep]
    if job_name:
        lines.insert(0, f"Priorities — {job_name}")
        lines.insert(1, "")
    if not entries:
        lines.append("(no priorities set)")
    else:
        for entry in entries:
            lines.append(render_priority_row(entry))
    return "\n".join(lines)


def print_priority_table(entries: List[dict], job_name: str = "") -> None:
    """Print the priority table to stdout."""
    print(render_priority_table(entries, job_name))
