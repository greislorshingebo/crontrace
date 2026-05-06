"""Integration tests for the CLI, including the new prune sub-command."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from crontrace.cli import _build_parser, cmd_prune, cmd_run, main
from crontrace.storage import get_connection


@pytest.fixture()
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "crontrace_test.db")


def _insert_old(db: str, job: str, days_ago: int) -> None:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    ts = dt.strftime("%Y-%m-%dT%H:%M:%S")
    conn = get_connection(db)
    conn.execute(
        "INSERT INTO executions (job_name, started_at, duration_s, exit_code) VALUES (?,?,?,?)",
        (job, ts, 0.5, 0),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Existing CLI tests
# ---------------------------------------------------------------------------

def test_cli_run_success(db_path):
    rc = main(["--db", db_path, "run", "echo_job", "echo", "hello"])
    # main calls sys.exit; capture via SystemExit
    with pytest.raises(SystemExit) as exc:
        main(["--db", db_path, "run", "echo_job", "echo", "hello"])
    assert exc.value.code == 0


def test_cli_run_failure_propagates_exit_code(db_path):
    with pytest.raises(SystemExit) as exc:
        main(["--db", db_path, "run", "bad_job", "false"])
    assert exc.value.code != 0


def test_cli_run_records_are_stored(db_path):
    with pytest.raises(SystemExit):
        main(["--db", db_path, "run", "stored_job", "echo", "ok"])
    conn = get_connection(db_path)
    rows = conn.execute("SELECT job_name FROM executions").fetchall()
    conn.close()
    assert any(r[0] == "stored_job" for r in rows)


def test_cli_log_prints_output(db_path, capsys):
    with pytest.raises(SystemExit):
        main(["--db", db_path, "run", "log_job", "echo", "hi"])
    with pytest.raises(SystemExit):
        main(["--db", db_path, "log"])
    captured = capsys.readouterr()
    assert "log_job" in captured.out


# ---------------------------------------------------------------------------
# Prune sub-command tests
# ---------------------------------------------------------------------------

def test_cli_prune_removes_old_records(db_path, capsys):
    _insert_old(db_path, "nightly", days_ago=40)
    _insert_old(db_path, "nightly", days_ago=2)

    with pytest.raises(SystemExit) as exc:
        main(["--db", db_path, "prune", "--days", "30"])
    assert exc.value.code == 0

    conn = get_connection(db_path)
    rows = conn.execute("SELECT * FROM executions").fetchall()
    conn.close()
    assert len(rows) == 1


def test_cli_prune_output_message(db_path, capsys):
    _insert_old(db_path, "weekly", days_ago=60)

    with pytest.raises(SystemExit):
        main(["--db", db_path, "prune", "--days", "30", "--job", "weekly"])

    captured = capsys.readouterr()
    assert "weekly" in captured.out
    assert "1" in captured.out


def test_cli_prune_no_match_zero_deleted(db_path, capsys):
    _insert_old(db_path, "fresh", days_ago=1)

    with pytest.raises(SystemExit):
        main(["--db", db_path, "prune", "--days", "30"])

    captured = capsys.readouterr()
    assert "0" in captured.out
