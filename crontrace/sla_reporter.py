"""Render SLA definitions and evaluation results for terminal output."""

from __future__ import annotations

from typing import Optional

_COL_JOB = 28
_COL_MAX_DUR = 10
_COL_MIN_RATE = 10
_COL_NOTE = 24


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    return value[: width - 1] + "…"


def _fmt_rate(rate: Optional[float]) -> str:
    if rate is None:
        return "—"
    return f"{rate * 100:.0f}%"


def _fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds / 60:.1f}m"


def _ok_label(ok: bool) -> str:
    return "✓" if ok else "✗"


def render_sla_row(entry: dict) -> str:
    """Format a single SLA definition row (no evaluation)."""
    job = _truncate(entry["job_name"], _COL_JOB)
    max_dur = _fmt_duration(entry["max_duration"])
    min_rate = _fmt_rate(entry["min_success_rate"])
    note = _truncate(entry.get("note") or "", _COL_NOTE)
    return (
        f"{job:<{_COL_JOB}}  "
        f"{max_dur:>{_COL_MAX_DUR}}  "
        f"{min_rate:>{_COL_MIN_RATE}}  "
        f"{note}"
    )


def render_sla_table(entries: list[dict]) -> str:
    """Render all SLA definitions as a plain-text table."""
    header = (
        f"{'JOB':<{_COL_JOB}}  "
        f"{'MAX DUR':>{_COL_MAX_DUR}}  "
        f"{'MIN RATE':>{_COL_MIN_RATE}}  "
        f"NOTE"
    )
    sep = "-" * (len(header) + 4)
    lines = [header, sep]
    if not entries:
        lines.append("  (no SLAs configured)")
    else:
        lines.extend(render_sla_row(e) for e in entries)
    return "\n".join(lines)


def render_sla_evaluation(job_name: str, sla: dict, result: dict) -> str:
    """Render an SLA evaluation result for a single job."""
    dur_icon = _ok_label(result["duration_ok"])
    rate_icon = _ok_label(result["success_rate_ok"])
    avg = _fmt_duration(result["avg_duration"])
    rate = _fmt_rate(result["success_rate"])
    max_dur = _fmt_duration(sla["max_duration"])
    min_rate = _fmt_rate(sla["min_success_rate"])
    lines = [
        f"SLA evaluation: {job_name}",
        f"  Duration    {dur_icon}  avg={avg} (limit={max_dur})",
        f"  Success rate {rate_icon}  actual={rate} (min={min_rate})",
    ]
    return "\n".join(lines)


def print_sla_table(entries: list[dict]) -> None:  # pragma: no cover
    print(render_sla_table(entries))
