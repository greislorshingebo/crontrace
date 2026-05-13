"""Tests for crontrace.job_aliases."""

import sqlite3
import pytest

from crontrace.job_aliases import (
    set_alias,
    get_alias,
    delete_alias,
    list_aliases,
    aliases_for_job,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_alias_returns_none_when_missing(conn):
    assert get_alias(conn, "nightly") is None


def test_set_and_get_alias_round_trip(conn):
    set_alias(conn, "nightly", "backup-job")
    assert get_alias(conn, "nightly") == "backup-job"


def test_alias_is_lowercased_on_set(conn):
    set_alias(conn, "NightlyBACKUP", "backup-job")
    assert get_alias(conn, "nightlybackup") == "backup-job"


def test_get_alias_is_case_insensitive(conn):
    set_alias(conn, "deploy", "deploy-job")
    assert get_alias(conn, "DEPLOY") == "deploy-job"


def test_set_alias_overwrites_existing(conn):
    set_alias(conn, "daily", "old-job")
    set_alias(conn, "daily", "new-job")
    assert get_alias(conn, "daily") == "new-job"


def test_delete_alias_returns_true_when_found(conn):
    set_alias(conn, "weekly", "report-job")
    assert delete_alias(conn, "weekly") is True
    assert get_alias(conn, "weekly") is None


def test_delete_alias_returns_false_when_missing(conn):
    assert delete_alias(conn, "ghost") is False


def test_list_aliases_empty_when_none(conn):
    assert list_aliases(conn) == []


def test_list_aliases_returns_all_entries(conn):
    set_alias(conn, "b-alias", "job-b")
    set_alias(conn, "a-alias", "job-a")
    result = list_aliases(conn)
    assert len(result) == 2
    assert result[0]["alias"] == "a-alias"
    assert result[1]["alias"] == "b-alias"


def test_list_aliases_contains_job_name(conn):
    set_alias(conn, "quick", "fast-job")
    result = list_aliases(conn)
    assert result[0]["job_name"] == "fast-job"


def test_aliases_for_job_returns_empty_when_none(conn):
    assert aliases_for_job(conn, "nonexistent") == []


def test_aliases_for_job_returns_all_matching(conn):
    set_alias(conn, "alpha", "shared-job")
    set_alias(conn, "beta", "shared-job")
    set_alias(conn, "gamma", "other-job")
    result = aliases_for_job(conn, "shared-job")
    assert sorted(result) == ["alpha", "beta"]


def test_aliases_for_job_independent_per_job(conn):
    set_alias(conn, "x", "job-x")
    set_alias(conn, "y", "job-y")
    assert aliases_for_job(conn, "job-x") == ["x"]
    assert aliases_for_job(conn, "job-y") == ["y"]
