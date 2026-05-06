"""Report: render a human-readable summary table for a job."""

from __future__ import annotations

from typing import Any

from crontrace.summarizer import summarize

_WIDTH = 36


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _dur(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 60:
        return f"{value:.2f}s"
    minutes, seconds = divmod(value, 60)
    return f"{int(minutes)}m {seconds:.0f}s"


def _line(label: str, value: str) -> str:
    return f"  {label:<18}{value}"


def render_summary(job_name: str, rows: list[tuple[Any, ...]]) -> str:
    """Return a formatted multi-line summary string for *job_name*."""
    stats = summarize(rows)
    sep = "-" * _WIDTH
    last_exit = stats["last_exit"]
    status_str = "n/a" if last_exit is None else ("OK" if last_exit == 0 else f"FAIL ({last_exit})")

    lines = [
        sep,
        f"  Job: {job_name}",
        sep,
        _line("Total runs:", str(stats["total"])),
        _line("Successes:", str(stats["successes"])),
        _line("Failures:", str(stats["failures"])),
        _line("Success rate:", _pct(stats["success_rate"])),
        _line("Avg duration:", _dur(stats["avg_duration"])),
        _line("Min duration:", _dur(stats["min_duration"])),
        _line("Max duration:", _dur(stats["max_duration"])),
        _line("Last status:", status_str),
        sep,
    ]
    return "\n".join(lines)
