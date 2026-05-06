"""Replay module: re-run a historical cron job command from the execution log."""

import subprocess
from typing import Optional

from crontrace.storage import get_connection, insert_execution
from crontrace.runner import _now_utc


def fetch_execution(db_path: str, execution_id: int) -> Optional[dict]:
    """Fetch a single execution record by its rowid."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT rowid, job_name, command, exit_code, started_at, duration_s"
            " FROM executions WHERE rowid = ?",
            (execution_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None
    return {
        "id": row[0],
        "job_name": row[1],
        "command": row[2],
        "exit_code": row[3],
        "started_at": row[4],
        "duration_s": row[5],
    }


def replay_execution(
    db_path: str,
    execution_id: int,
    record: bool = True,
) -> int:
    """Re-run the command from a historical execution.

    Args:
        db_path: Path to the SQLite database.
        execution_id: rowid of the execution to replay.
        record: If True, persist the new run to the database.

    Returns:
        The exit code of the replayed command.

    Raises:
        ValueError: If the execution_id is not found.
    """
    entry = fetch_execution(db_path, execution_id)
    if entry is None:
        raise ValueError(f"No execution found with id {execution_id}")

    command = entry["command"]
    job_name = entry["job_name"]

    started_at = _now_utc()
    t0 = __import__("time").monotonic()
    result = subprocess.run(command, shell=True)
    duration_s = __import__("time").monotonic() - t0

    if record:
        conn = get_connection(db_path)
        try:
            insert_execution(conn, job_name, command, result.returncode, started_at, duration_s)
        finally:
            conn.close()

    return result.returncode
