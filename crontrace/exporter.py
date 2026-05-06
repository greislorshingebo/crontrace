"""Export execution history to JSON or CSV formats."""

from __future__ import annotations

import csv
import io
import json
from typing import List, Dict, Any


def _rows_to_dicts(rows: List[Any]) -> List[Dict[str, Any]]:
    """Convert sqlite3.Row objects (or tuples) to plain dicts."""
    result = []
    for row in rows:
        try:
            result.append(dict(row))
        except TypeError:
            # fallback for plain tuples: (id, job, started_at, duration_s, exit_code)
            result.append({
                "id": row[0],
                "job": row[1],
                "started_at": row[2],
                "duration_s": row[3],
                "exit_code": row[4],
            })
    return result


def export_json(rows: List[Any], indent: int = 2) -> str:
    """Serialize execution records to a JSON string."""
    return json.dumps(_rows_to_dicts(rows), indent=indent)


def export_csv(rows: List[Any]) -> str:
    """Serialize execution records to a CSV string."""
    dicts = _rows_to_dicts(rows)
    if not dicts:
        return ""

    fieldnames = ["id", "job", "started_at", "duration_s", "exit_code"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(dicts)
    return buf.getvalue()
