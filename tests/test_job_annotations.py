"""Tests for crontrace.job_annotations."""

import sqlite3

import pytest

from crontrace.job_annotations import (
    add_annotation,
    annotations_for_job,
    delete_annotation,
    get_annotations,
)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    yield c
    c.close()


def test_add_annotation_returns_rowid(conn):
    rowid = add_annotation(conn, exec_id=1, job_name="backup", note="manual rerun")
    assert isinstance(rowid, int)
    assert rowid >= 1


def test_get_annotations_empty_when_none(conn):
    result = get_annotations(conn, exec_id=99)
    assert result == []


def test_get_annotations_returns_added_note(conn):
    add_annotation(conn, exec_id=5, job_name="sync", note="all good")
    rows = get_annotations(conn, exec_id=5)
    assert len(rows) == 1
    assert rows[0]["note"] == "all good"
    assert rows[0]["job_name"] == "sync"
    assert rows[0]["exec_id"] == 5


def test_get_annotations_multiple_ordered_oldest_first(conn):
    add_annotation(conn, exec_id=3, job_name="job", note="first")
    add_annotation(conn, exec_id=3, job_name="job", note="second")
    rows = get_annotations(conn, exec_id=3)
    assert [r["note"] for r in rows] == ["first", "second"]


def test_get_annotations_isolated_by_exec_id(conn):
    add_annotation(conn, exec_id=1, job_name="job", note="for exec 1")
    add_annotation(conn, exec_id=2, job_name="job", note="for exec 2")
    assert len(get_annotations(conn, exec_id=1)) == 1
    assert len(get_annotations(conn, exec_id=2)) == 1


def test_delete_annotation_returns_true_on_success(conn):
    ann_id = add_annotation(conn, exec_id=7, job_name="prune", note="temp")
    assert delete_annotation(conn, ann_id) is True
    assert get_annotations(conn, exec_id=7) == []


def test_delete_annotation_returns_false_when_missing(conn):
    assert delete_annotation(conn, annotation_id=9999) is False


def test_annotations_for_job_returns_all_executions(conn):
    add_annotation(conn, exec_id=1, job_name="deploy", note="run 1")
    add_annotation(conn, exec_id=2, job_name="deploy", note="run 2")
    add_annotation(conn, exec_id=3, job_name="other", note="unrelated")
    rows = annotations_for_job(conn, "deploy")
    assert len(rows) == 2
    assert all(r["job_name"] == "deploy" for r in rows)


def test_annotations_for_job_newest_first(conn):
    add_annotation(conn, exec_id=10, job_name="report", note="older")
    add_annotation(conn, exec_id=11, job_name="report", note="newer")
    rows = annotations_for_job(conn, "report")
    assert rows[0]["note"] == "newer"


def test_add_annotation_strips_whitespace(conn):
    add_annotation(conn, exec_id=4, job_name="trim", note="  padded  ")
    rows = get_annotations(conn, exec_id=4)
    assert rows[0]["note"] == "padded"


def test_add_annotation_raises_on_empty_note(conn):
    with pytest.raises(ValueError):
        add_annotation(conn, exec_id=1, job_name="job", note="   ")
