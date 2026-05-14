"""Render archived execution records for display."""

from typing import Sequence

_COL_WIDTHS = {"job_name": 24, "started_at": 22, "duration": 10, "exit_code": 9, "archived_at": 22}


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _fmt_duration(duration) -> str:
    if duration is None:
        return "-"
    return f"{duration:.2f}s"


def _fmt_exit(code: int) -> str:
    return "OK" if code == 0 else f"FAIL({code})"


def render_archive_row(entry: dict) -> str:
    job = _truncate(entry.get("job_name", ""), _COL_WIDTHS["job_name"])
    started = _truncate(entry.get("started_at", ""), _COL_WIDTHS["started_at"])
    dur = _fmt_duration(entry.get("duration"))
    code = _fmt_exit(entry.get("exit_code", 0))
    archived = _truncate(entry.get("archived_at", ""), _COL_WIDTHS["archived_at"])
    return (
        f"{job:<24}  {started:<22}  {dur:<10}  {code:<9}  {archived:<22}"
    )


def render_archive_table(job_name: str, rows: Sequence[dict]) -> str:
    header = (
        f"{'JOB':<24}  {'STARTED':<22}  {'DURATION':<10}  {'STATUS':<9}  {'ARCHIVED':<22}"
    )
    separator = "-" * len(header)
    title = f"Archive: {job_name}  ({len(rows)} record(s))"
    lines = [title, separator, header, separator]
    if not rows:
        lines.append("  (no archived records)")
    else:
        lines.extend(render_archive_row(r) for r in rows)
    lines.append(separator)
    return "\n".join(lines)


def print_archive_table(job_name: str, rows: Sequence[dict]) -> None:
    print(render_archive_table(job_name, rows))
