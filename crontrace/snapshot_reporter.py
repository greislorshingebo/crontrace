"""Render job snapshots as human-readable text tables."""

from typing import List, Optional

_COL_JOB = 28
_COL_CODE = 6
_COL_DUR = 10
_COL_AT = 22


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _fmt_exit(code: Optional[int]) -> str:
    if code is None:
        return "  -  "
    return " OK " if code == 0 else f" {code} "


def _fmt_duration(dur: Optional[float]) -> str:
    if dur is None:
        return "   -   "
    return f"{dur:.2f}s"


def _header() -> str:
    return (
        f"{'JOB':<{_COL_JOB}}  "
        f"{'CODE':>{_COL_CODE}}  "
        f"{'DURATION':>{_COL_DUR}}  "
        f"{'CAPTURED AT':<{_COL_AT}}"
    )


def render_snapshot_row(entry: dict) -> str:
    """Format a single snapshot *entry* dict as a table row."""
    job = _truncate(entry.get("job_name") or "", _COL_JOB)
    code = _fmt_exit(entry.get("exit_code"))
    dur = _fmt_duration(entry.get("duration"))
    at = _truncate(entry.get("captured_at") or "", _COL_AT)
    return f"{job:<{_COL_JOB}}  {code:>{_COL_CODE}}  {dur:>{_COL_DUR}}  {at:<{_COL_AT}}"


def render_snapshot_table(entries: List[dict], job_name: Optional[str] = None) -> str:
    """Return a full table string for *entries*.  Optionally prefix a title."""
    title = f"Snapshots for {job_name}" if job_name else "All Snapshots"
    sep = "-" * ((_COL_JOB + _COL_CODE + _COL_DUR + _COL_AT) + 6)
    lines = [title, sep, _header(), sep]
    if not entries:
        lines.append("  (no snapshots stored)")
    else:
        for entry in entries:
            lines.append(render_snapshot_row(entry))
    lines.append(sep)
    return "\n".join(lines)


def print_snapshots(entries: List[dict], job_name: Optional[str] = None) -> None:
    print(render_snapshot_table(entries, job_name))
