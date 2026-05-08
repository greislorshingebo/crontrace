"""Tests for crontrace.job_labels."""

import sqlite3
import pytest

from crontrace.job_labels import (
    set_label,
    set_labels_bulk,
    get_label,
    get_labels,
    delete_label,
    jobs_by_label,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_get_label_returns_none_when_missing(conn):
    assert get_label(conn, "myjob", "env") is None


def test_set_and_get_label_round_trip(conn):
    set_label(conn, "myjob", "env", "prod")
    assert get_label(conn, "myjob", "env") == "prod"


def test_set_label_overwrites_existing(conn):
    set_label(conn, "myjob", "env", "staging")
    set_label(conn, "myjob", "env", "prod")
    assert get_label(conn, "myjob", "env") == "prod"


def test_set_label_key_is_lowercased(conn):
    set_label(conn, "myjob", "ENV", "prod")
    assert get_label(conn, "myjob", "env") == "prod"


def test_set_label_independent_per_job(conn):
    set_label(conn, "job-a", "env", "prod")
    set_label(conn, "job-b", "env", "staging")
    assert get_label(conn, "job-a", "env") == "prod"
    assert get_label(conn, "job-b", "env") == "staging"


def test_get_labels_empty_when_none(conn):
    assert get_labels(conn, "myjob") == {}


def test_get_labels_returns_all_keys(conn):
    set_labels_bulk(conn, "myjob", {"env": "prod", "team": "infra", "tier": "1"})
    labels = get_labels(conn, "myjob")
    assert labels == {"env": "prod", "team": "infra", "tier": "1"}


def test_set_labels_bulk_overwrites_existing(conn):
    set_label(conn, "myjob", "env", "staging")
    set_labels_bulk(conn, "myjob", {"env": "prod", "team": "data"})
    assert get_label(conn, "myjob", "env") == "prod"
    assert get_label(conn, "myjob", "team") == "data"


def test_delete_label_removes_key(conn):
    set_label(conn, "myjob", "env", "prod")
    deleted = delete_label(conn, "myjob", "env")
    assert deleted is True
    assert get_label(conn, "myjob", "env") is None


def test_delete_label_returns_false_when_missing(conn):
    assert delete_label(conn, "myjob", "nonexistent") is False


def test_delete_label_does_not_affect_other_keys(conn):
    set_labels_bulk(conn, "myjob", {"env": "prod", "team": "infra"})
    delete_label(conn, "myjob", "env")
    assert get_label(conn, "myjob", "team") == "infra"


def test_jobs_by_label_returns_matching_jobs(conn):
    set_label(conn, "job-a", "env", "prod")
    set_label(conn, "job-b", "env", "prod")
    set_label(conn, "job-c", "env", "staging")
    result = jobs_by_label(conn, "env", "prod")
    assert sorted(result) == ["job-a", "job-b"]


def test_jobs_by_label_empty_when_no_match(conn):
    set_label(conn, "job-a", "env", "staging")
    assert jobs_by_label(conn, "env", "prod") == []


def test_jobs_by_label_deduplicates(conn):
    # Same job should appear only once even if it has multiple matching labels
    set_label(conn, "job-a", "env", "prod")
    result = jobs_by_label(conn, "env", "prod")
    assert result.count("job-a") == 1
