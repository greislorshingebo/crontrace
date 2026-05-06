"""diff_reporter.py – compare two execution records and report changes."""
from __future__ import annotations

from typing import Any, Dict, Optional


# Keys we care about when diffing two execution records
_COMPARE_KEYS = ("exit_code", "duration", "stdout", "stderr")


def diff_executions(
    old: Dict[str, Any],
    new: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Return a mapping of field -> {old, new} for every field that changed.

    Only compares the keys listed in ``_COMPARE_KEYS``.
    """
    changes: Dict[str, Dict[str, Any]] = {}
    for key in _COMPARE_KEYS:
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            changes[key] = {"old": old_val, "new": new_val}
    return changes


def _status_label(exit_code: Optional[int]) -> str:
    if exit_code is None:
        return "UNKNOWN"
    return "OK" if exit_code == 0 else f"FAIL({exit_code})"


def render_diff(
    job_name: str,
    old: Dict[str, Any],
    new: Dict[str, Any],
) -> str:
    """Return a human-readable diff report between two execution records."""
    changes = diff_executions(old, new)
    if not changes:
        return f"[{job_name}] No changes between executions."

    lines = [f"[{job_name}] Execution diff ({old.get('started_at')} → {new.get('started_at')})"]
    for field, delta in changes.items():
        if field == "exit_code":
            old_label = _status_label(delta["old"])
            new_label = _status_label(delta["new"])
            lines.append(f"  exit_code : {old_label} → {new_label}")
        elif field == "duration":
            old_d = delta["old"]
            new_d = delta["new"]
            old_s = f"{old_d:.2f}s" if old_d is not None else "n/a"
            new_s = f"{new_d:.2f}s" if new_d is not None else "n/a"
            lines.append(f"  duration  : {old_s} → {new_s}")
        else:
            old_str = str(delta["old"]) if delta["old"] is not None else ""
            new_str = str(delta["new"]) if delta["new"] is not None else ""
            # Truncate long values for readability
            old_str = (old_str[:60] + "…") if len(old_str) > 60 else old_str
            new_str = (new_str[:60] + "…") if len(new_str) > 60 else new_str
            lines.append(f"  {field:<10}: {old_str!r} → {new_str!r}")
    return "\n".join(lines)
