"""Integration tests for the crontrace CLI."""

import sqlite3
import pytest
from pathlib import Path

from crontrace.cli import main
from crontrace.storage import get_connection, fetch_recent


@pytest.fixture()
def db_path(tmp_path) -> Path:
    return tmp_path / "test_history.db"


def test_cli_run_success(db_path):
    exit_code = main(["run", "--db", str(db_path), "echo", "hello"])
    assert exit_code == 0


def test_cli_run_failure_propagates_exit_code(db_path):
    exit_code = main(["run", "--db", str(db_path), "false"])
    assert exit_code != 0


def test_cli_run_records_are_stored(db_path):
    main(["run", "--db", str(db_path), "echo", "stored"])
    conn = get_connection(str(db_path))
    records = fetch_recent(conn, limit=10)
    conn.close()
    assert len(records) == 1
    assert "echo" in records[0]["command"]


def test_cli_log_prints_output(db_path, capsys):
    main(["run", "--db", str(db_path), "echo", "log_test"])
    exit_code = main(["log", "--db", str(db_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "echo" in captured.out


def test_cli_log_missing_db_returns_error(tmp_path, capsys):
    missing = tmp_path / "nonexistent.db"
    exit_code = main(["log", "--db", str(missing)])
    assert exit_code == 1


def test_cli_run_no_command_returns_error(db_path, capsys):
    exit_code = main(["run", "--db", str(db_path)])
    assert exit_code == 2


def test_cli_log_limit_respected(db_path, capsys):
    for i in range(5):
        main(["run", "--db", str(db_path), "echo", str(i)])
    main(["log", "--db", str(db_path), "--limit", "3"])
    captured = capsys.readouterr()
    assert "3 record(s) shown" in captured.out
