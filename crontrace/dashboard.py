"""Terminal dashboard: renders a compact multi-job status overview."""

from __future__ import annotations

from typing import List, Tuple

from crontrace.summarizer import summarize
from crontrace.alerting import evaluate_alerts
from crontrace.report import render_summary
from crontrace.alert_reporter import render_alerts

_HEADER = "="* 60
_SEP = "-" * 60


def _section(title: str) -> str:
    return f"\n{_HEADER}\n  {title}\n{_HEADER}"


def render_job_panel(
    job_name: str,
    rows: list,
    failure_rate_threshold: float = 0.5,
    avg_duration_threshold: float = 300.0,
) -> str:
    """Return a formatted panel string for a single job."""
    lines: List[str] = []
    lines.append(_section(f"Job: {job_name}"))

    summary = summarize(job_name, rows)
    lines.append(render_summary(summary))

    alerts = evaluate_alerts(
        job_name,
        rows,
        failure_rate_threshold=failure_rate_threshold,
        avg_duration_threshold=avg_duration_threshold,
    )
    if alerts:
        lines.append("")
        lines.append("Alerts:")
        lines.append(render_alerts(alerts))

    return "\n".join(lines)


def render_dashboard(
    jobs: List[Tuple[str, list]],
    failure_rate_threshold: float = 0.5,
    avg_duration_threshold: float = 300.0,
) -> str:
    """Render a full dashboard for multiple jobs.

    Args:
        jobs: list of (job_name, rows) tuples.
        failure_rate_threshold: alert if failure rate exceeds this fraction.
        avg_duration_threshold: alert if avg duration (seconds) exceeds this.

    Returns:
        A single string suitable for printing to a terminal.
    """
    if not jobs:
        return "No jobs to display."

    panels = [
        render_job_panel(
            name,
            rows,
            failure_rate_threshold=failure_rate_threshold,
            avg_duration_threshold=avg_duration_threshold,
        )
        for name, rows in jobs
    ]
    return ("\n" + _SEP).join(panels)
