"""Render job environment variables for terminal display."""

from typing import Dict

_COL_KEY = 28
_COL_VAL = 48


def _truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def render_env_row(key: str, value: str) -> str:
    """Format a single key/value pair as a fixed-width table row."""
    k = _truncate(key, _COL_KEY)
    v = _truncate(value, _COL_VAL)
    return f"  {k:<{_COL_KEY}}  {v}"


def render_env_table(job_name: str, env: Dict[str, str]) -> str:
    """Render a full environment table for *job_name*."""
    header = f"Environment variables for job: {job_name}"
    separator = "-" * (2 + _COL_KEY + 2 + _COL_VAL)
    col_header = render_env_row("KEY", "VALUE")

    if not env:
        body = "  (no variables stored)"
    else:
        body = "\n".join(render_env_row(k, v) for k, v in sorted(env.items()))

    return "\n".join([header, separator, col_header, separator, body, separator])


def print_env_table(job_name: str, env: Dict[str, str]) -> None:
    """Print the environment table to stdout."""
    print(render_env_table(job_name, env))
