"""Render search results for terminal output."""

from __future__ import annotations

from typing import Any

_COL_WIDTHS = {"job_name": 24, "started_at": 20, "exit_code": 9, "duration_s": 10}
_HEADER = (
    f"{'JOB':<24}  {'STARTED':<20}  {'CODE':>9}  {'DURATION':>10}"
)
_SEP = "-" * len(_HEADER)


def _fmt_row(row: dict[str, Any]) -> str:
    name = str(row.get("job_name", ""))[:24]
    started = str(row.get("started_at", ""))[:20]
    code = str(row.get("exit_code", ""))
    dur = row.get("duration_s")
    dur_str = f"{float(dur):.2f}s" if dur is not None else "\u2014"
    return f"{name:<24}  {started:<20}  {code:>9}  {dur_str:>10}"


def render_search_results(
    rows: list[dict[str, Any]],
    query_description: str = "",
) -> str:
    """Return a formatted table string for *rows*.

    Args:
        rows: A list of result dicts, each expected to contain the keys
            ``job_name``, ``started_at``, ``exit_code``, and ``duration_s``.
        query_description: Optional human-readable description of the search
            query, printed as a header line above the table.

    Returns:
        A multi-line string suitable for printing to a terminal.
    """
    lines: list[str] = []
    if query_description:
        lines.append(f"Search: {query_description}")
    lines.append(_HEADER)
    lines.append(_SEP)
    if not rows:
        lines.append("  (no results)")
    else:
        for row in rows:
            lines.append(_fmt_row(row))
    lines.append(_SEP)
    lines.append(f"{len(rows)} result(s)")
    return "\n".join(lines)


def print_search_results(
    rows: list[dict[str, Any]],
    query_description: str = "",
) -> None:
    """Print formatted search results to stdout.

    Convenience wrapper around :func:`render_search_results`.
    """
    print(render_search_results(rows, query_description))
