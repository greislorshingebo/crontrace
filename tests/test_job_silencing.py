import sqlite3
import pytest
from crontrace.job_silencing import (
    silence_job,
    unsilence_job,
    get_silencing,
    list_silenced,
    is_silenced,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_silencing_returns_none_when_missing(conn):
    assert get_silencing(conn, "backup") is None


def test_is_silenced_false_when_missing(conn):
    assert is_silenced(conn, "backup") is False


def test_silence_and_get_round_trip(conn):
    silence_job(conn, "backup", reason="maintenance", note="planned downtime")
    result = get_silencing(conn, "backup")
    assert result is not None
    assert result["job_name"] == "backup"
    assert result["reason"] == "maintenance"
    assert result["note"] == "planned downtime"
    assert result["silenced_at"]  # non-empty timestamp


def test_is_silenced_true_after_silence(conn):
    silence_job(conn, "report")
    assert is_silenced(conn, "report") is True


def test_silence_overwrites_existing(conn):
    silence_job(conn, "etl", reason="flapping", note="first")
    silence_job(conn, "etl", reason="expected", note="second")
    result = get_silencing(conn, "etl")
    assert result["reason"] == "expected"
    assert result["note"] == "second"


def test_unsilence_removes_entry(conn):
    silence_job(conn, "deploy")
    removed = unsilence_job(conn, "deploy")
    assert removed is True
    assert get_silencing(conn, "deploy") is None


def test_unsilence_returns_false_when_not_silenced(conn):
    assert unsilence_job(conn, "nonexistent") is False


def test_list_silenced_empty_returns_empty(conn):
    assert list_silenced(conn) == []


def test_list_silenced_returns_all_entries(conn):
    silence_job(conn, "job_b", reason="other")
    silence_job(conn, "job_a", reason="maintenance")
    entries = list_silenced(conn)
    assert len(entries) == 2
    # ordered by job_name
    assert entries[0]["job_name"] == "job_a"
    assert entries[1]["job_name"] == "job_b"


def test_silence_invalid_reason_raises(conn):
    with pytest.raises(ValueError, match="Invalid reason"):
        silence_job(conn, "job", reason="unknown")


def test_silence_empty_job_name_raises(conn):
    with pytest.raises(ValueError, match="job_name must not be empty"):
        silence_job(conn, "   ")


def test_silence_strips_whitespace_from_job_name(conn):
    silence_job(conn, "  trimmed  ")
    assert is_silenced(conn, "trimmed") is True


def test_silence_note_defaults_to_none(conn):
    silence_job(conn, "nightly")
    result = get_silencing(conn, "nightly")
    assert result["note"] is None


def test_list_silenced_excludes_unsilenced(conn):
    silence_job(conn, "a")
    silence_job(conn, "b")
    unsilence_job(conn, "a")
    entries = list_silenced(conn)
    assert len(entries) == 1
    assert entries[0]["job_name"] == "b"
