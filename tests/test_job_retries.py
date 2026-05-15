"""Tests for crontrace.job_retries."""

import sqlite3
import pytest

from crontrace.job_retries import (
    set_retry_policy,
    get_retry_policy,
    delete_retry_policy,
    list_retry_policies,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_retry_policy_returns_none_when_missing(conn):
    assert get_retry_policy(conn, "backup") is None


def test_set_and_get_round_trip(conn):
    set_retry_policy(conn, "backup", max_retries=3, retry_delay=30)
    policy = get_retry_policy(conn, "backup")
    assert policy is not None
    assert policy["job_name"] == "backup"
    assert policy["max_retries"] == 3
    assert policy["retry_delay"] == 30


def test_set_retry_policy_with_note(conn):
    set_retry_policy(conn, "sync", max_retries=5, retry_delay=120, note="flaky network")
    policy = get_retry_policy(conn, "sync")
    assert policy["note"] == "flaky network"


def test_note_defaults_to_none(conn):
    set_retry_policy(conn, "cleanup", max_retries=2)
    policy = get_retry_policy(conn, "cleanup")
    assert policy["note"] is None


def test_retry_delay_defaults_to_sixty(conn):
    set_retry_policy(conn, "report", max_retries=1)
    policy = get_retry_policy(conn, "report")
    assert policy["retry_delay"] == 60


def test_set_retry_policy_overwrites_existing(conn):
    set_retry_policy(conn, "backup", max_retries=2, retry_delay=30)
    set_retry_policy(conn, "backup", max_retries=5, retry_delay=90, note="updated")
    policy = get_retry_policy(conn, "backup")
    assert policy["max_retries"] == 5
    assert policy["retry_delay"] == 90
    assert policy["note"] == "updated"


def test_set_retry_policy_independent_per_job(conn):
    set_retry_policy(conn, "job_a", max_retries=1)
    set_retry_policy(conn, "job_b", max_retries=9)
    assert get_retry_policy(conn, "job_a")["max_retries"] == 1
    assert get_retry_policy(conn, "job_b")["max_retries"] == 9


def test_delete_retry_policy_returns_true_when_exists(conn):
    set_retry_policy(conn, "backup", max_retries=3)
    assert delete_retry_policy(conn, "backup") is True


def test_delete_retry_policy_returns_false_when_missing(conn):
    assert delete_retry_policy(conn, "ghost") is False


def test_delete_removes_record(conn):
    set_retry_policy(conn, "backup", max_retries=3)
    delete_retry_policy(conn, "backup")
    assert get_retry_policy(conn, "backup") is None


def test_list_retry_policies_empty(conn):
    assert list_retry_policies(conn) == []


def test_list_retry_policies_returns_all(conn):
    set_retry_policy(conn, "beta", max_retries=2)
    set_retry_policy(conn, "alpha", max_retries=4)
    policies = list_retry_policies(conn)
    assert len(policies) == 2
    assert policies[0]["job_name"] == "alpha"
    assert policies[1]["job_name"] == "beta"


def test_negative_max_retries_raises(conn):
    with pytest.raises(ValueError, match="max_retries"):
        set_retry_policy(conn, "bad", max_retries=-1)


def test_negative_retry_delay_raises(conn):
    with pytest.raises(ValueError, match="retry_delay"):
        set_retry_policy(conn, "bad", max_retries=3, retry_delay=-5)


def test_job_name_is_stripped(conn):
    set_retry_policy(conn, "  trimmed  ", max_retries=1)
    assert get_retry_policy(conn, "trimmed") is not None
    assert get_retry_policy(conn, "  trimmed  ") is not None
