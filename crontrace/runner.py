"""Core runner: wraps a shell command, captures timing and exit code, stores the result."""

import subprocess
import shlex
from datetime import datetime, timezone

from crontrace.storage import get_connection, insert_execution


ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def run_job(
    command: str,
    job_name: str,
    db_path=None,
    timeout: int | None = None,
) -> int:
    """
    Execute *command* in a subprocess, record the outcome, and return the exit code.

    Parameters
    ----------
    command:  Shell command string to execute.
    job_name: Human-readable label stored alongside the record.
    db_path:  Override the default database location (useful for testing).
    timeout:  Optional subprocess timeout in seconds.
    """
    started_at = _now_utc()

    try:
        result = subprocess.run(
            shlex.split(command),
            timeout=timeout,
            capture_output=False,
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124  # same convention as the `timeout` shell utility
    except FileNotFoundError:
        exit_code = 127  # command not found

    finished_at = _now_utc()
    duration_s = (finished_at - started_at).total_seconds()

    record = {
        "job_name": job_name,
        "command": command,
        "started_at": started_at.strftime(ISO_FMT),
        "finished_at": finished_at.strftime(ISO_FMT),
        "duration_s": round(duration_s, 3),
        "exit_code": exit_code,
    }

    kwargs = {"db_path": db_path} if db_path else {}
    conn = get_connection(**kwargs)
    insert_execution(conn, record)
    conn.close()

    return exit_code
