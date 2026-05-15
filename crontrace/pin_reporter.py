"""Render job pin records as human-readable text."""

from typing import List

_COL_JOB = 28
_COL_RUN = 8
_COL_NOTE = 30
_COL_TS = 22


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _header() -> str:
    job_h = "JOB".ljust(_COL_JOB)
    run_h = "RUN ID".ljust(_COL_RUN)
    note_h = "NOTE".ljust(_COL_NOTE)
    ts_h = "PINNED AT".ljust(_COL_TS)
    sep = "-" * (_COL_JOB + _COL_RUN + _COL_NOTE + _COL_TS + 3)
    return f"{job_h} {run_h} {note_h} {ts_h}\n{sep}"


def render_pin_row(entry: dict) -> str:
    """Format a single pin *entry* dict as a fixed-width line."""
    job = _truncate(entry.get("job_name") or "", _COL_JOB).ljust(_COL_JOB)
    run_id = str(entry.get("run_id") or "").ljust(_COL_RUN)
    note = _truncate(entry.get("note") or "-", _COL_NOTE).ljust(_COL_NOTE)
    ts = _truncate(entry.get("pinned_at") or "", _COL_TS).ljust(_COL_TS)
    return f"{job} {run_id} {note} {ts}"


def render_pin_table(entries: List[dict]) -> str:
    """Return a formatted table string for a list of pin entries."""
    if not entries:
        return "No pinned executions."
    lines = [_header()]
    for entry in entries:
        lines.append(render_pin_row(entry))
    return "\n".join(lines)


def print_pins(entries: List[dict]) -> None:  # pragma: no cover
    print(render_pin_table(entries))
