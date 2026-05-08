"""Render job labels as a human-readable table."""

from typing import Dict, List, Tuple

_KEY_W = 20
_VAL_W = 30


def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def render_label_row(key: str, value: str) -> str:
    """Format a single key/value pair as a fixed-width table row."""
    return f"  {_truncate(key, _KEY_W):<{_KEY_W}}  {_truncate(value, _VAL_W)}"


def render_label_table(job_name: str, labels: Dict[str, str]) -> str:
    """Render all labels for *job_name* as a plain-text table."""
    header = f"Labels for job: {job_name}"
    separator = "-" * (4 + _KEY_W + 2 + _VAL_W)
    col_header = f"  {'KEY':<{_KEY_W}}  {'VALUE'}"

    if not labels:
        return "\n".join([header, separator, "  (no labels)"])

    rows = [render_label_row(k, v) for k, v in sorted(labels.items())]
    return "\n".join([header, separator, col_header, separator] + rows)


def print_label_table(job_name: str, labels: Dict[str, str]) -> None:  # pragma: no cover
    """Print the label table to stdout."""
    print(render_label_table(job_name, labels))
