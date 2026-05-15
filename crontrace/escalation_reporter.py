"""Render escalation policies as a human-readable table."""

from typing import List

_HEADER = f"{'JOB':<30} {'THRESHOLD':>9} {'ENABLED':>7} {'CONTACT':<25} NOTE"
_SEP = "-" * 85


def _truncate(value: str, width: int) -> str:
    if value is None:
        return "-"
    return value if len(value) <= width else value[: width - 1] + "…"


def _enabled_label(enabled: bool) -> str:
    return "yes" if enabled else "no"


def render_escalation_row(entry: dict) -> str:
    """Format a single escalation policy dict as a fixed-width string."""
    job = _truncate(entry.get("job_name", ""), 30)
    threshold = entry.get("threshold", 3)
    enabled = _enabled_label(entry.get("enabled", True))
    contact = _truncate(entry.get("contact"), 25)
    note = _truncate(entry.get("note"), 30)
    return f"{job:<30} {threshold:>9} {enabled:>7} {contact:<25} {note}"


def render_escalation_table(entries: List[dict]) -> str:
    """Return a full table string for a list of escalation policy dicts."""
    if not entries:
        return "No escalation policies defined."
    lines = [_HEADER, _SEP]
    for entry in entries:
        lines.append(render_escalation_row(entry))
    return "\n".join(lines)


def print_escalation_table(entries: List[dict]) -> None:  # pragma: no cover
    print(render_escalation_table(entries))
