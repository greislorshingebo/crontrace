"""Render job quota information as a human-readable table."""

from typing import List

_COL_JOB = 30
_COL_MAX = 10
_COL_WIN = 8


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _header() -> str:
    job_h = "JOB".ljust(_COL_JOB)
    max_h = "MAX RUNS".ljust(_COL_MAX)
    win_h = "WINDOW".ljust(_COL_WIN)
    line = f"{job_h}  {max_h}  {win_h}"
    sep = "-" * len(line)
    return f"{line}\n{sep}"


def render_quota_row(entry: dict) -> str:
    """Format a single quota dict as a table row string."""
    job = _truncate(entry.get("job_name", ""), _COL_JOB).ljust(_COL_JOB)
    max_runs = str(entry.get("max_runs", "")).ljust(_COL_MAX)
    window = _truncate(entry.get("window", ""), _COL_WIN).ljust(_COL_WIN)
    return f"{job}  {max_runs}  {window}"


def render_quota_table(entries: List[dict]) -> str:
    """Render a list of quota dicts as a formatted table string."""
    if not entries:
        return "No quotas configured."
    lines = [_header()]
    for entry in entries:
        lines.append(render_quota_row(entry))
    return "\n".join(lines)


def print_quota_table(entries: List[dict]) -> None:  # pragma: no cover
    print(render_quota_table(entries))
