"""Render trigger records as human-readable text tables."""

from typing import Optional

_ICONS = {
    "manual": "✋",
    "dependency": "🔗",
    "webhook": "🌐",
    "schedule": "🕐",
}

_COL_WIDTHS = {"id": 6, "job_name": 24, "trigger": 12, "note": 28, "fired_at": 22}


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _icon(trigger: str) -> str:
    return _ICONS.get(trigger, "❓")


def render_trigger_row(entry: dict) -> str:
    """Format a single trigger dict as a table row string."""
    note = entry.get("note") or "-"
    trigger = entry.get("trigger", "")
    parts = [
        str(entry.get("id", "")).ljust(_COL_WIDTHS["id"]),
        _truncate(entry.get("job_name", ""), _COL_WIDTHS["job_name"]).ljust(
            _COL_WIDTHS["job_name"]
        ),
        f"{_icon(trigger)} {trigger}".ljust(_COL_WIDTHS["trigger"] + 3),
        _truncate(note, _COL_WIDTHS["note"]).ljust(_COL_WIDTHS["note"]),
        entry.get("fired_at", ""),
    ]
    return "  ".join(parts)


def render_trigger_table(job_name: Optional[str], entries: list[dict]) -> str:
    """Render a full table with header for the given trigger entries."""
    header_title = f"Triggers for: {job_name}" if job_name else "All Triggers"
    header = (
        "ID    ".ljust(_COL_WIDTHS["id"])
        + "  "
        + "JOB".ljust(_COL_WIDTHS["job_name"])
        + "  "
        + "TYPE".ljust(_COL_WIDTHS["trigger"] + 3)
        + "  "
        + "NOTE".ljust(_COL_WIDTHS["note"])
        + "  FIRED AT"
    )
    separator = "-" * len(header)
    lines = [header_title, separator, header, separator]
    if not entries:
        lines.append("  (no trigger records found)")
    else:
        for entry in entries:
            lines.append(render_trigger_row(entry))
    lines.append(separator)
    return "\n".join(lines)


def print_triggers(job_name: Optional[str], entries: list[dict]) -> None:
    print(render_trigger_table(job_name, entries))
