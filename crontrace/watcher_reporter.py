"""Render job watcher lists as human-readable text tables."""

from typing import List

_HEADER = f"{'JOB':<30} {'WATCHER':<30} {'NOTIFY ON':<10} {'ADDED AT'}"
_SEP = "-" * 85

_ICONS = {"failure": "⚠", "success": "✓", "always": "★"}


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def render_watcher_row(entry: dict) -> str:
    job = _truncate(entry.get("job_name", ""), 30)
    watcher = _truncate(entry.get("watcher", ""), 30)
    notify_on = entry.get("notify_on", "failure")
    icon = _ICONS.get(notify_on, "?")
    added_at = entry.get("added_at", "")
    return f"{job:<30} {watcher:<30} {icon} {notify_on:<8} {added_at}"


def render_watcher_table(job_name: str, entries: List[dict]) -> str:
    if not entries:
        return f"No watchers registered for '{job_name}'."
    lines = [f"Watchers for job: {job_name}", _SEP, _HEADER, _SEP]
    for entry in entries:
        lines.append(render_watcher_row(entry))
    lines.append(_SEP)
    lines.append(f"{len(entries)} watcher(s) total.")
    return "\n".join(lines)


def print_watchers(job_name: str, entries: List[dict]) -> None:
    print(render_watcher_table(job_name, entries))
