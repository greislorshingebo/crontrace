"""Render job hook information as text tables."""

from typing import List

_HOOK_TYPE_WIDTH = 6
_COMMAND_MAX = 48
_STATUS_WIDTH = 8


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _enabled_label(enabled: bool) -> str:
    return "ON " if enabled else "OFF"


def render_hook_row(hook: dict) -> str:
    """Render a single hook as a formatted line."""
    hook_type = hook["hook_type"].upper().ljust(_HOOK_TYPE_WIDTH)
    command = _truncate(hook["command"], _COMMAND_MAX).ljust(_COMMAND_MAX)
    status = _enabled_label(hook["enabled"]).ljust(_STATUS_WIDTH)
    return f"  {hook_type}  {command}  [{status}]"


def render_hook_table(job_name: str, hooks: List[dict]) -> str:
    """Render all hooks for a job as a text block."""
    lines = [f"Hooks for job: {job_name}"]
    if not hooks:
        lines.append("  (no hooks configured)")
        return "\n".join(lines)

    header = "  " + "TYPE  ".ljust(_HOOK_TYPE_WIDTH) + "  " + "COMMAND".ljust(_COMMAND_MAX) + "  STATUS"
    lines.append(header)
    lines.append("  " + "-" * (_HOOK_TYPE_WIDTH + _COMMAND_MAX + _STATUS_WIDTH + 6))
    for hook in hooks:
        lines.append(render_hook_row(hook))
    return "\n".join(lines)


def print_hooks(job_name: str, hooks: List[dict]) -> None:  # pragma: no cover
    print(render_hook_table(job_name, hooks))
