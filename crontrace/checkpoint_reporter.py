"""Render checkpoint data as human-readable text tables."""

from typing import List

_HEADER = f"{'ID':>6}  {'RUN ID':<24}  {'CHECKPOINT':<20}  {'REACHED AT':<22}  NOTE"
_SEP = "-" * 90


def _truncate(text: str, width: int) -> str:
    if text is None:
        return ""
    return text if len(text) <= width else text[: width - 1] + "…"


def render_checkpoint_row(entry: dict) -> str:
    """Format a single checkpoint dict as a table row string."""
    cp_id = entry.get("id", "")
    run_id = _truncate(str(entry.get("run_id", "")), 24)
    name = _truncate(str(entry.get("name", "")), 20)
    reached_at = _truncate(str(entry.get("reached_at", "")), 22)
    note = _truncate(str(entry.get("note", "") or ""), 30)
    return f"{cp_id:>6}  {run_id:<24}  {name:<20}  {reached_at:<22}  {note}"


def render_checkpoint_table(job_name: str, entries: List[dict]) -> str:
    """Render a full checkpoint table for a job."""
    lines = [f"Checkpoints for job: {job_name}", _SEP, _HEADER, _SEP]
    if not entries:
        lines.append("  (no checkpoints recorded)")
    else:
        for entry in entries:
            lines.append(render_checkpoint_row(entry))
    lines.append(_SEP)
    return "\n".join(lines)


def print_checkpoints(job_name: str, entries: List[dict]) -> None:
    """Print the checkpoint table to stdout."""
    print(render_checkpoint_table(job_name, entries))
