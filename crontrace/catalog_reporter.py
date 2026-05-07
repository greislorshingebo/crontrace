"""Render job catalog entries as human-readable text."""

from typing import List

_COL_WIDTHS = {
    "job_name": 24,
    "command": 32,
    "schedule": 14,
    "owner": 12,
}


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value.ljust(width)
    return value[: width - 1] + "…"


def render_catalog_row(entry: dict) -> str:
    """Format a single catalog entry as a fixed-width line."""
    job = _truncate(entry.get("job_name") or "", _COL_WIDTHS["job_name"])
    cmd = _truncate(entry.get("command") or "", _COL_WIDTHS["command"])
    sched = _truncate(entry.get("schedule") or "-", _COL_WIDTHS["schedule"])
    owner = _truncate(entry.get("owner") or "-", _COL_WIDTHS["owner"])
    desc = entry.get("description") or ""
    return f"{job}  {cmd}  {sched}  {owner}  {desc}"


def render_catalog_table(entries: List[dict]) -> str:
    """Render a list of catalog entries as a table with a header."""
    header = (
        _truncate("JOB NAME", _COL_WIDTHS["job_name"]) + "  "
        + _truncate("COMMAND", _COL_WIDTHS["command"]) + "  "
        + _truncate("SCHEDULE", _COL_WIDTHS["schedule"]) + "  "
        + _truncate("OWNER", _COL_WIDTHS["owner"]) + "  "
        + "DESCRIPTION"
    )
    separator = "-" * len(header)
    if not entries:
        return "\n".join([header, separator, "(no jobs registered)"])
    rows = [render_catalog_row(e) for e in entries]
    return "\n".join([header, separator] + rows)


def print_catalog(entries: List[dict]) -> None:  # pragma: no cover
    print(render_catalog_table(entries))
