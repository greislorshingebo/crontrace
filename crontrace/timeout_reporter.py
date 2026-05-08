"""Render timeout configuration as human-readable tables."""

from typing import Sequence

_COL_JOB = 30
_COL_TIMEOUT = 12
_COL_UPDATED = 22


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def render_timeout_row(entry: dict) -> str:
    """Format a single timeout entry as a fixed-width string."""
    job = _truncate(entry.get("job_name", ""), _COL_JOB)
    secs = str(entry.get("timeout_s", ""))
    updated = entry.get("updated_at", "") or ""
    return f"{job:<{_COL_JOB}}  {secs:>{_COL_TIMEOUT}}s  {updated:<{_COL_UPDATED}}"


def _header() -> str:
    job_h = f"{'JOB':<{_COL_JOB}}"
    to_h = f"{'TIMEOUT (s)':>{_COL_TIMEOUT + 1}}"
    up_h = f"{'UPDATED':<{_COL_UPDATED}}"
    sep = "-" * (_COL_JOB + _COL_TIMEOUT + _COL_UPDATED + 6)
    return f"{job_h}  {to_h}  {up_h}\n{sep}"


def render_timeout_table(entries: Sequence[dict]) -> str:
    """Return a multi-line table string for *entries*."""
    if not entries:
        return "No timeout rules configured."
    lines = [_header()]
    for entry in entries:
        lines.append(render_timeout_row(entry))
    return "\n".join(lines)


def print_timeouts(entries: Sequence[dict]) -> None:  # pragma: no cover
    print(render_timeout_table(entries))
