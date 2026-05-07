"""Tests for crontrace.job_catalog."""

import sqlite3
import pytest

from crontrace.job_catalog import (
    register_job,
    get_job,
    list_jobs,
    deregister_job,
)


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_job_returns_none_when_missing(conn):
    assert get_job(conn, "nonexistent") is None


def test_register_and_get_round_trip(conn):
    register_job(conn, "backup", "/bin/backup.sh", schedule="0 2 * * *", owner="ops")
    entry = get_job(conn, "backup")
    assert entry is not None
    assert entry["job_name"] == "backup"
    assert entry["command"] == "/bin/backup.sh"
    assert entry["schedule"] == "0 2 * * *"
    assert entry["owner"] == "ops"


def test_register_overwrites_existing(conn):
    register_job(conn, "backup", "/bin/old.sh")
    register_job(conn, "backup", "/bin/new.sh", owner="dev")
    entry = get_job(conn, "backup")
    assert entry["command"] == "/bin/new.sh"
    assert entry["owner"] == "dev"


def test_list_jobs_empty_returns_empty_list(conn):
    assert list_jobs(conn) == []


def test_list_jobs_returns_all_entries(conn):
    register_job(conn, "zzz", "/bin/zzz.sh")
    register_job(conn, "aaa", "/bin/aaa.sh")
    jobs = list_jobs(conn)
    assert len(jobs) == 2
    assert jobs[0]["job_name"] == "aaa"
    assert jobs[1]["job_name"] == "zzz"


def test_list_jobs_ordered_alphabetically(conn):
    names = ["delta", "alpha", "gamma", "beta"]
    for n in names:
        register_job(conn, n, f"/bin/{n}.sh")
    result = [j["job_name"] for j in list_jobs(conn)]
    assert result == sorted(names)


def test_deregister_existing_job_returns_true(conn):
    register_job(conn, "cleanup", "/bin/cleanup.sh")
    assert deregister_job(conn, "cleanup") is True
    assert get_job(conn, "cleanup") is None


def test_deregister_missing_job_returns_false(conn):
    assert deregister_job(conn, "ghost") is False


def test_optional_fields_default_to_none(conn):
    register_job(conn, "minimal", "/bin/minimal.sh")
    entry = get_job(conn, "minimal")
    assert entry["schedule"] is None
    assert entry["description"] is None
    assert entry["owner"] is None


def test_created_at_is_populated(conn):
    register_job(conn, "job1", "/bin/job1.sh")
    entry = get_job(conn, "job1")
    assert entry["created_at"] is not None
    assert len(entry["created_at"]) > 0
